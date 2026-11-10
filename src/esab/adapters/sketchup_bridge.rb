# SketchUp Ruby 桥接扩展
#
# 本文件是一个 SketchUp 插件。用户把它放到 SketchUp 的 Plugins 目录：
#   Windows: C:\Users\<user>\AppData\Roaming\SketchUp\SketchUp 2026\SketchUp\Plugins\
#
# SketchUp 启动时自动加载本文件。它在后台 TCPServer 监听 127.0.0.1:49999，
# 接受长度前缀 JSON 消息，在 SketchUp 模型上下文中 eval Ruby 代码。
#
# 协议：
#   请求: [4 字节大端长度][UTF-8 JSON body]
#   body: {"id": "...", "method": "run|status|wait|summary",
#          "code": "...", "vars": {...}, "operation": "...", "timeout": 120}
#   响应: [4 字节大端长度][UTF-8 JSON body]
#   body: {"id": "...", "ok": true, "result": ..., "stdout": "..."}
#         {"id": "...", "ok": false, "error": "..."}

require 'socket'
require 'json'
require 'thread'

module SketchupBridge
  HOST = '127.0.0.1'
  PORT = 49999
  @server = nil
  @thread = nil
  @jobs = {}
  @jobs_mutex = Mutex.new

  def self.start
    return if @thread && @thread.alive?

    @thread = Thread.new do
      begin
        @server = TCPServer.new(HOST, PORT)
      rescue Errno::EADDRINUSE
        # 端口被占，静默退出
        next
      end

      loop do
        begin
          client = @server.accept
          Thread.new(client) do |c|
            handle_client(c)
          end
        rescue
          next
        end
      end
    end
  end

  def self.handle_client(client)
    # 读 4 字节长度前缀
    len_bytes = recv_all(client, 4)
    return unless len_bytes && len_bytes.bytesize == 4
    len = len_bytes.unpack1('N')
    return if len <= 0 || len > 64 * 1024 * 1024

    body_bytes = recv_all(client, len)
    return unless body_bytes && body_bytes.bytesize == len

    req = JSON.parse(body_bytes, symbolize_names: true)
    resp = dispatch(req)
    send_msg(client, resp)
    client.close
  rescue => e
    begin
      send_msg(client, { id: req[:id] rescue nil, ok: false, error: e.message })
      client.close
    rescue
    end
  end

  def self.recv_all(sock, n)
    data = +''
    while data.bytesize < n
      chunk = sock.recv(n - data.bytesize)
      return nil if chunk.empty?
      data << chunk
    end
    data
  end

  def self.send_msg(sock, obj)
    body = JSON.generate(obj)
    sock.write([body.bytesize].pack('N'))
    sock.write(body)
  end

  def self.dispatch(req)
    id = req[:id]
    method = req[:method].to_s

    case method
    when 'run'
      run_code(id, req)
    when 'status'
      { id: id, ok: true, result: { busy: !@jobs.empty? } }
    when 'wait'
      job_id = req[:job_id]
      # 简单等待：轮询作业表
      120.times do
        break unless @jobs[job_id]
        sleep 0.5
      end
      { id: id, ok: true, result: @jobs.delete(job_id) }
    when 'summary'
      summarize
    else
      { id: id, ok: false, error: "unknown method: #{method}" }
    end
  end

  def self.run_code(id, req)
    code = req[:code].to_s
    vars = req[:vars] || {}
    operation = req[:operation]

    model = Sketchup.active_model

    # 用 start_operation/commit_operation 包裹，支持撤销
    result = nil
    error = nil
    stdout = +''

    if operation
      model.start_operation(operation.to_s, true)
    end

    begin
      # 把 vars 注入为 Ruby 局部变量（用 binding 不好实现，改用 Object 实例 eval）
      obj = Object.new
      vars.each do |k, v|
        obj.instance_variable_set("@#{k}", v)
      end
      # 简化：把 vars 作为局部变量通过 binding eval 不可靠，直接在代码前注入赋值
      prefix = vars.map { |k, v| "#{k} = #{v.inspect}" }.join("\n")
      full_code = prefix + "\n" + code

      # 捕获 stdout
      old_stdout = $stdout
      $stdout = StringIO.new
      begin
        result = obj.instance_eval(full_code)
      ensure
        stdout = $stdout.string
        $stdout = old_stdout
      end

      if operation
        model.commit_operation
      end
    rescue => e
      error = "#{e.class}: #{e.message}\n#{e.backtrace.first(5).join("\n")}"
      if operation
        model.abort_operation
      end
    end

    if error
      { id: id, ok: false, error: error, result: { stdout: stdout } }
    else
      { id: id, ok: true, result: serialize(result), stdout: stdout }
    end
  end

  def self.summarize
    model = Sketchup.active_model
    ents = model.entities
    {
      id: nil,
      ok: true,
      result: {
        path: model.path,
        title: model.title,
        units: model.options['UnitsOptions']['LengthUnit'],
        entity_count: ents.length,
      }
    }
  end

  # 序列化 Ruby 对象为 JSON 友好的纯数据
  def self.serialize(obj)
    case obj
    when nil, true, false, Numeric, String
      obj
    when Array
      obj.map { |e| serialize(e) }
    when Hash
      obj.transform_keys(&:to_s).transform_values { |v| serialize(v) }
    when Geom::Point3d
      { x: obj.x.mm, y: obj.y.mm, z: obj.z.mm }
    when Geom::Vector3d
      { x: obj.x, y: obj.y, z: obj.z }
    else
      obj.inspect
    end
  end
end

# SketchUp 启动时自动加载
if defined?(Sketchup) && Sketchup.active_model
  SketchupBridge.start
else
  # 在模型加载完成后启动
  UI.start_timer(1.0, false) { SketchupBridge.start }
end

kill_process() {
    # 使用 ps -elf 查找包含关键词的进程，并提取 PID
    pids=$(ps -elf | grep "$1" | grep -v grep | awk '{print $4}')

    # 检查是否有匹配的进程
    if [ -z "$pids" ]; then
        echo "没有找到匹配的进程"
        return 1
    fi

    # 将 PID 转换为数组
    pids_array=($pids)

    # 检查 PID 是否有效
    for pid in "${pids_array[@]}"; do
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "无效的进程 ID: $pid"
            return 1
        fi
    done

    # 列出将要终止的进程
    echo "将要终止以下进程:"
    ps -p "${pids_array[*]}" -o pid,cmd

    # 确认是否继续
    read -p "确认终止这些进程吗？(y/n): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "终止操作已取消"
        return 0
    fi

    # 终止进程
    kill "${pids_array[@]}"
    echo "已终止进程: ${pids_array[*]}"
}

bg_run() {
    if [ $# -eq 0 ]; then
        echo "Usage: bg_run <command> [args...]"
        return 1
    fi

    local prefix="run"
    local timestamp
    timestamp=$(date +"%Y%m%d_%H%M%S")
    local log_file="${prefix}_${timestamp}_$$.log"

    # 把执行命令记录到日志文件开头
    {
        echo "===== bg_run started ====="
        echo "Time : $(date)"
        echo "PID  : TBD (assigned after nohup)"
        echo "Cmd  : $*"
        echo "==========================="
        echo
    } > "$log_file"

    # 后台执行命令
    nohup "$@" >> "$log_file" 2>&1 &
    local pid=$!

    # 回写 PID（可选）
    sed -i "s/PID  : TBD (assigned after nohup)/PID  : $pid/" "$log_file"

    echo "Background process started:"
    echo "  PID: $pid"
    echo "  Log: $log_file"

    echo "$pid"
}

alias ifconfig="ipconfig"

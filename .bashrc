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
    local log_file="run_$$.log"
    nohup "$@" > "$log_file" 2>&1 &
    echo "Background process started with PID $! - Log file: $log_file"
}


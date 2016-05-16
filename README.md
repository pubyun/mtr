


如果提示错误：

    mtr: unable to get raw sockets

则执行下属命令：

    setcap cap_net_raw+ep /usr/sbin/mtr
    getcap /usr/sbin/mtr

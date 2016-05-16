# mtr.py，使用mtr测试网络质量

一个Python程序，使用mtr来测试、记录网络延时，并且进行分析。

## 安装说明

    git clone https://github.com/pubyun/mtr.git
    yum -y install mtr tmux
    setcap cap_net_raw+ep /usr/sbin/mtr
    getcap /usr/sbin/mtr

## 使用方法

### 监测主机

修改 hosts.txt 文件。注意IP地址和说明之间要用空格分开。

### 监测记录

    python mtr.py

### 分析日志

#### 生成网络丢包的报告

    python mtr.py log > report.txt

#### 对检测主机的丢包情况排序

    grep timeout report.txt |sort -n -k 4


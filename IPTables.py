import os
import subprocess


def is_root():
    return os.geteuid() == 0


def run_cmd(cmd, debug=False):
    if debug:
        print("Running command [" + cmd + "]")
    subprocess.call(cmd.split(" "), stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)


def run_question(question):
    yes = ['y', 'yes', '']
    msg = " [y/Y = Yes*] [n/N = No] "
    tmp = input("\n" + question + msg)
    tmp = tmp.lower()
    if tmp in yes:
        return True
    return False


def check_line_in_file(search_line, file):
    with open(file, 'r+') as logfile:
        for line in logfile:
            if line.strip() == search_line:
                return True
    return False


if __name__ == '__main__':
    if not is_root():
        print("This script must be run as root to interact with IPTables and APT.")
        exit(0)

    print("\nI provide no warranty for this script, use at your own risk.")
    if not run_question("I agree"):
        exit(0)

    print("\nRunning APT Update")
    run_cmd("apt update")

    if run_question("Would you like to upgrade packages?"):
        print("Upgrading APT Packages")
        run_cmd("apt upgrade -y")

    print("Installing IPTables Persistent")
    run_cmd("apt install iptables-persistent -y")

    print("Installing basic IPTable rules")
    run_cmd("iptables -F")
    run_cmd("iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP")
    run_cmd("iptables -A INPUT -p tcp ! --syn -m state --state NEW -j DROP")
    run_cmd("iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP")
    run_cmd("iptables -A INPUT -i lo -j ACCEPT")

    to_question = [
        # SSH
        ["SSH", [22], []],
        # HTTP
        ["HTTP", [80], []],
        # HTTPS
        ["HTTPS", [443], []],
        # SMTP
        ["SMTP", [25, 465], []],
        # POP 3
        ["POP3", [110, 995], []],
        # IMAP
        ["IMAP", [143, 993], []],
        # Home Assistant
        ["Home Assistant", [8123], []]
    ]

    for question in to_question:
        if run_question("Unblock " + question[0] + "?"):
            print("Unblocking " + question[0])
            if len(question[1]) > 0:
                for p in question[1]:
                    print("Unblocking TCP Port [" + str(p) + "]")
                    run_cmd("iptables -A INPUT -p tcp -m tcp --dport " + str(p) + " -j ACCEPT")

            if len(question[2]) > 0:
                for p in question[2]:
                    print("Unblocking UDP Port [" + str(p) + "]")
                    run_cmd("iptables -A INPUT -p udp -m udp --dport " + str(p) + " -j ACCEPT")

    run_cmd("iptables -I INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT")
    run_cmd("iptables -P OUTPUT ACCEPT")
    run_cmd("iptables -P INPUT DROP")

    run_cmd("iptables-save >/etc/iptables/rules.v4")
    run_cmd("ip6tables-save >/etc/iptables/rules.v6")

    if os.path.exists("/etc/rc.local") and not check_line_in_file("iptables-restore < /etc/iptables.rules", "/etc/rc.local"):
        run_cmd("head -n -1 /etc/rc.local > temp_iptables.txt")
        run_cmd("echo 'iptables-restore < /etc/iptables/rules.v4' >> temp_iptables.txt")
        run_cmd("echo 'exit 0' >> temp_iptables.txt")
        run_cmd("mv temp_iptables.txt /etc/rc.local")
        run_cmd("rm temp_iptables.txt")

    print("IPTable setup complete!")

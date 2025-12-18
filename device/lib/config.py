""" module to configure the device depending on user input in configuration file """
import os
import time
import debounce

datafilebase="/sd/measurement"

class config:
    """ configuration to e read from file """
    def __init__(self, filename="/sd/configuration"):
        self.filename=filename
        self.starttime=None
        self.reset()
        self.startblock=True
        self.button_1=debounce.button(14, 12, label="1", fnc=self.button_check)
        self.button_2=debounce.button(15, 13, label="2", fnc=self.button_check)
        self.buttonclicks={}
        self.buttonclicks["1"]=0
        self.buttonclicks["2"]=0
        # self.read_config()
        return

    def reset(self):
        self.startcondition={}
        self.stopcondition={}
        self.startblock=False
        self.buttonclicks=0
        self.datarate_a=0
        self.datarate_t=0
        self.comment=""
        self.metadata=""
        return

    def proc_datarate(self, s):
        index=s.find('-')
        if index != -1:
            self.datarate_a=s[:index].lstrip().rstrip()
            self.datarate_t=s[index+1:].lstrip().rstrip()
        return

    def proc_metadata(self, s):
        self.metadata=s
        return

    def proc_condition(self, s):
        index=s.find('[')
        ctime=0
        state=""
        if index != -1:
            state=s[index+1:s.find(']')]
            if "s" in state:
                ctime=int(state[:-1])
            if "m" in state:
                ctime=60*int(state[:-1])
            if "h" in state:
                ctime=3600*int(state[:-1])
            if state == "on":
                state="on"
            if state == "off":
                state="off"
        return (s[:index], state, ctime)

    def button_check(self,l,v):
        #if PRINT:
        #    print("%s %s" % (l, self.buttonclicks[l]))
        self.buttonclicks[l]=self.buttonclicks[l]+1
        if self.startcondition["C"] == "button"+l:
            if self.startcondition["S"] == "off" and v == 0 and self.buttonclicks[l]==1:
                time.sleep(0.2)
                self.buttonclicks[l]=2
            if self.startcondition["S"] == "off" and v == 1 and self.buttonclicks[l]>1:
                self.startblock=False
                self.buttonclicks[l]=0
                return
            if self.startcondition["S"] == "on" and v == 1 and self.buttonclicks[l]==1:
                time.sleep(0.2)
                self.buttonclicks=2
            if self.startcondition["S"] == "on" and v == 0 and self.buttonclicks[l]>1:
                self.startblock=False
                self.buttonclicks[l]=0
                return
        self.startblock=True

    def wait_until_start(self, led):
        if self.startcondition["C"].startswith("button"):
            l=0
            while self.startblock:
                if l==0:
                    led.on()
                else:
                    led.off()
                time.sleep(0.1)
                l=l+1
                if l>9:
                    l=0
            # put small sequence here
            for l in self.buttonclicks:
                self.buttonclicks[l]=0
            pass
        if self.startcondition["C"] == "time":
            time.sleep(self.startcondition["T"])
        self.starttime=time.time()
        return True

    def run_condition(self):
        delta=0
        if self.stopcondition["C"].startswith("button"):
            return self.buttonclicks[self.stopcondition["C"][6]]==0
        if self.stopcondition["C"] == "time":
            delta=self.stopcondition["T"]
            if time.time()-self.starttime<delta:
                return True
        return False

    def read_config(self):
        try:
            f_config = os.stat(self.filename)
        except OSError:
            f_config = None
        comment=""
        state=""
        # create new, default file, if not existant
        if f_config is None:
            with open(self.filename, "w") as file:
                file.write("Metadata: taken on XYZ by A, B\n")
                file.write("StartCondition: button1[off]\n")
                file.write("StopCondition:  button2[on]\n")
                file.write("# alternative StopCondition:  time[30s]\n")
                file.write("DataRate(A/T):  3 - 1\n")
            time.sleep(0.05)
        # file exists
        with open(self.filename, "r") as file:
            for line in file:
                comment=""
                state=""
                cpline=""
                cline=line.strip()
                if cline.startswith("#"):
                    self.comment+=cline
                if cline.startswith("StartCondition:"):
                    cpline=cline[15:].lstrip()
                    (cond,stat,ctime) = self.proc_condition(cpline)
                    self.startcondition={ "C": cond, "S": stat, "T": ctime }
                if cline.startswith("StopCondition:"):
                    cpline=cline[14:].lstrip()
                    (cond,stat,ctime) = self.proc_condition(cpline)
                    self.stopcondition={ "C": cond, "S": stat, "T": ctime }
                if cline.startswith("DataRate(A/T):"):
                    cpline=cline[14:].lstrip()
                    self.proc_datarate(cpline)
                if cline.startswith("Metadata:"):
                    cpline=cline[9:].lstrip()
                    self.proc_metadata(cpline)
                print(cline + ":: " + comment + " :")

    def next_datafile(self,base=datafilebase):
        for s in range(1000,2000):
            tfname = base+str(s).replace('1','.',1)
            try:
                tf = os.stat(tfname)
            except OSError:
                return tfname

def main():
    c = config()

    print(c.comment)
    print("# StartCondition: ", end="")
    print(c.startcondition)
    print("# StopCondition : ", end="")
    print(c.stopcondition)
    print("# DataRate(A/T) : ", end="")
    print(c.datarate_a, end=" - ")
    print(c.datarate_t)
    print("")

    print("test start @ ", end='')
    ts=time.time()
    print(ts)
    c.wait_until_start()
    print("measurement @ ", end='')
    tm=time.time()
    print(tm)

    while c.run_condition():
        time.sleep(0.5)
    print("test stop  @ ", end='')
    te=time.time()
    print(te)
    print("  delta   ", end='')
    print(te-ts)
    print("  delta m ", end='')
    print(tm-ts)
if __name__ == "__main__":
    main()
###################
# StartCondition: button<n> / time / sensor(?) / accel(?) / BLE(?)
# StopCondition:  button<n> / time / sensor(?) / accel(?) / BLE(?)
# DataRate(A/T):  freq + freq
###################

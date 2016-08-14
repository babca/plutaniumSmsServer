#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import logging
import signal
import traceback

import time
from tempfile import gettempdir

from pep3143daemon import DaemonContext
from pep3143daemon import PidFile

from utils.configUtils import * ## global variable config[]

def create_dir(directory, do_log=True):
    """
    Creates a directory if it doesn't exists and write the execution in the logs
    """
    expanded_dir_name = os.path.expanduser(directory)
    try:
        if not os.path.isdir(expanded_dir_name):
            if do_log:
                logging.warning('[*] Directory {0} does not exists, creating...'.format(expanded_dir_name))
            os.makedirs(expanded_dir_name)
        else:
            if do_log:
                logging.warning('[*] Directory {0} found!'.format(expanded_dir_name))
    except Exception as error:
        err = '[*] Error while creating directory {0}: {1}'.format(expanded_dir_name, error)
        raise Exception(err)

# setups root logger, without custom name, comes with daemonized classes
def setup_logging(log_file, logging_level):

    class NoLogFilter(logging.Filter):
        def filter(self, record):
            return False

    def configure_logging(file_name):
        expanded_file_name = os.path.expanduser(file_name)
        expanded_dir_name = os.path.dirname(expanded_file_name)
        create_dir(expanded_dir_name, do_log=False)
        logging.basicConfig(
            filename=expanded_file_name,
            level=logging_level, # = loggin.DEBUG, logging.INFO, warning, error, critical...
            format=(u'[%(asctime)s] %(name)s %(levelname)s: %(message)s'))
        
        # pokud mame logovat jen INFO a vic, skryjeme z logu nektere Google API info zpravy, jsou zbytecne dlouhe
        if (logging_level >= logging.INFO): # debug=10, info=20, warning=30, error=40, critical=50
            log_filter = NoLogFilter()

            logging.getLogger("googleapiclient.discovery").addFilter(log_filter)

        # filter out some annoying messages
        # not the best position for this code

        #log_filter = NoLogFilter()
        #logging.getLogger("apscheduler.scheduler").addFilter(log_filter)
        #logging.getLogger("apscheduler.executors.default").addFilter(log_filter)
        #logging.getLogger("requests.packages.urllib3.connectionpool").addFilter(log_filter)  # the list is just an example
            
        return expanded_file_name

    log_file_paths = [log_file] if log_file else [
        myconfig['loggingSetup']['mainLogFilename'] ]
    for file_name in log_file_paths:
        try:
            return configure_logging(file_name)
        except IOError:
            pass

    raise Exception("Unable to write to log file") 

def setup_logger(logger_name, log_file, level=logging.INFO): # How to use: you have to get the logger in your namespace first: loggerSentSMS = logging.getLogger('sent_sms') ... then you can loggerSentSMS.info('LOG THIS INSANE EVENT!')

    """
    jina setupovaci trida na logging, nez setup_logging viz nize, tato podporuje vic loggeru. Puvodni zatim nechavame protoze je hluboko zakorenena v soucasnem kodu
    """

    formatter = logging.Formatter(u'[%(asctime)s] %(levelname)s: %(message)s')

    fileHandler   = logging.FileHandler(log_file, mode='a') # mode='w' = prepsat soubor, mode='a' = append
    streamHandler = logging.StreamHandler() # vraci odkaz na vystup na stderr. # Pozor aktualni bug kdyz se to zapne i pro demozovany skript spusteny na pozadi (start). Loguje to kam nema, do pid filu! Takze bud vyresit, nebo nejak povolit jen pro fg mod (foreground)

    fileHandler.setFormatter(formatter)
    streamHandler.setFormatter(formatter)

    l = logging.getLogger(logger_name)
    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)  



class NoDaemon:
    """
    A class which shares the same interface as the Daemon class,
    but is used to execute the scheduler as a foreground process

    """

    instance = None
    exit_flag = False

    def __init__(self, daemonizable):
        # daemonizable has to provide start/stop (and possibly reload) methods
        NoDaemon.instance = self
        self.daemonizable = daemonizable

        # register signal handlers
        for (signal_number, handler) in self.signal_map.items():
            signal.signal(signal_number, handler)

    @property
    def signal_map(self):
        return {
            signal.SIGTERM: NoDaemon.handle_program_exit,
            signal.SIGINT: NoDaemon.handle_program_exit,
            signal.SIGHUP: NoDaemon.handle_reload,
            }

    @staticmethod
    def handle_program_exit(signum, frame):
        logging.info('[*] Got signal {0}. Exiting ...'.format(signum))
        NoDaemon.exit_flag = True
        NoDaemon.instance.daemonizable.stop()

    @staticmethod
    def handle_reload(signum, frame):
        NoDaemon.instance.daemonizable.reload()

    def start(self, log_file=None, dump_stack_trace=False):
        setup_logging(log_file, myconfig['loggingSetup']['foregroundLogLevel']) # original logger, setups root logger, without custom name
        setup_logger('sent_sms', myconfig['loggingSetup']['sentSmsLogFilename'], logging.DEBUG) # my multilogger, always log sms (level INFO)

        while not NoDaemon.exit_flag:
            try:
                logging.info('[*] Starting in no-daemon mode')
                self.daemonizable.start()
                NoDaemon.exit_flag = True
            except Exception as e:
                if dump_stack_trace:
                    logging.error(traceback.format_exc(e))
                logging.error('[*] Restarting procedure in no-daemon mode after fatal error "{0}"'.format(e))
                time.sleep(10)
        logging.info('[*] Done exiting')

    def stop(self):
        pass

    def status(self):
        pass


class Daemon:
    """
    A class to manage all the daemon-related stuff

    """

    instance = None
    exit_flag = False

    def __init__(self, daemonizable=None, pid_fname=None):
        # daemonizable has to provide start/stop (and possibly reload) methods
        Daemon.instance = self
        self._pid_fname = pid_fname
        self.daemonizable = daemonizable

    @staticmethod
    def handle_program_exit(signum, frame):
        Daemon.exit_flag = True
        Daemon.instance.daemonizable.stop()

    @staticmethod
    def handle_reload(signum, frame):
        Daemon.instance.daemonizable.reload()

    @property
    def signal_map(self):
        return {
            signal.SIGTERM: Daemon.handle_program_exit,
            signal.SIGHUP: Daemon.handle_reload,
            }

    @property
    def pid_fname(self):
        if not self._pid_fname:
            fname = '{0}/smsserver_{1}.pid'.format(
                gettempdir(),
                os.path.split(os.path.expanduser('~'))[-1])
            self._pid_fname = os.path.normpath(fname)
        return self._pid_fname

    @property
    def pid(self):
        if os.path.isfile(self.pid_fname):
            with open(self.pid_fname, 'r') as f:
                pid = f.read()

                try:
                    return int(pid) # return "if pid is int". If not, an exception will be rised.
                    
                    print ('Running with pid: {0}'.format(pid))
                except ValueError:
                    print("The content of the pidfile is invalid!")
                    print(pid)
        return None

    def start(self, log_file=None, dump_stack_trace=False):
        pidfile = PidFile(self.pid_fname)
        pidfile.acquire()

        # setup pidfile
        # pidfile = PIDLockFile(self.pid_fname, timeout=-1) #PidFile(self.pid_fname)

        # try:
        #     pidfile.acquire()
        # except AlreadyLocked:
        #     try:
        #         os.kill(pidfile.read_pid(), 0)
        #         print 'Process already running.'
        #         return 1
        #     except OSError:  #No process with locked PID
        #         pidfile.break_lock()
        
        # pidfile can now be used to create DaemonContext:
        with DaemonContext(pidfile=pidfile, signal_map=self.signal_map):
            setup_logging(log_file, myconfig['loggingSetup']['daemonLogLevel']) # original logger, setups root logger, without custom name
            setup_logger('sent_sms', myconfig['loggingSetup']['sentSmsLogFilename']) # my multilogger, always log sms (level INFO)

            while not Daemon.exit_flag:
                try:
                    logging.info('[*] daemon starting, pid: {0}'.format(self.pid))
                    self.daemonizable.start()
                    Daemon.exit_flag = True
                except Exception as e:
                    if dump_stack_trace:
                        logging.error(traceback.format_exc(e))
                    logging.error('[*] Restarting daemonized procedure after Fatal Error: {0}'.format(e))
                    time.sleep(10)
            logging.info('[*] daemon done, pid: {0}'.format(self.pid))

    def stop(self):
        pid = self.pid

        if pid:
            try:
                int(pid) # "if pid is int". If not, an exception will be rised.
                
                os.kill(self.pid, signal.SIGTERM)
            except ValueError:
                print("The content of the pidfile is invalid!")
                print(pid)
        else:
            print ('Not Running')


    def status(self):
        pid = self.pid

        if pid:
            try:
                int(pid) # "if pid is int". If not, an exception will be rised.
                
                print ('Running with pid: {0}'.format(pid))
            except ValueError:
                print("The content of the pidfile is invalid!")
                print(pid)
        else:
            print ('Not Running')

    def reload(self, log_file=None, dump_stack_trace=False):
        print ('== RELOAD IS BUGGY ==')
        pid = self.pid

        if pid:
            try:
                int(pid) # "if pid is int". If not, an exception will be rised.
            
                os.kill(pid, signal.SIGHUP)
                
                time.sleep(5) # trochu hack, mozna by byl lepsi nejaky cyklus co kontroluje ukonceni daneho pidu, nebo tak neco
                # POZOR NEFUNGUJE SPRAVNE, NESTIHNE SE UKONCIT A NOVY SE NESPUSTI
                self.start(log_file=log_file, dump_stack_trace=dump_stack_trace) 
            except ValueError:
                print("The content of the pidfile is invalid!")
                print(pid)
        else:
            print ('Not Running')





import fcntl
import timeoutcontext
import os


class FileLock:
    '''
    Represents a file that can be opened and transparently locked.
    '''
    default_timeout = 10

    @staticmethod
    def set_default_timeout(timeout: int):
        __class__.default_timeout = timeout

    def __init__(self, file_name):
        '''
        The object is associated with one file name (path) for its lifetime.
        '''
        self.file_name = file_name
        self.fp = None  # file handle if the file is open
        self.exclusive = False

    def get_fp(self):
        '''
        Return file handle of opened file. None if the file is not open.
        '''
        return self.fp

    def exists(self) -> bool:
        return os.path.exists(self.file_name) and os.path.isfile(self.file_name)

    def is_open(self) -> bool:
        return self.fp is not None

    def is_exclusive(self) -> bool:
        return self.exclusive

    def get_file_name(self) -> str:
        return self.file_name

    def open(self, exclusive: bool = False, timeout: int | None = None) -> bool:
        '''
        Open and lock the file.
        Exclusive flag indicates rw mode and exclusive lock, otherwise readonly mode and shared lock is used.
        Timeout defines how long [s] should the function wait for the lock (0 = nonblocking, None = use default).
        Returns true if the file was opened and locked, false on timeout.
        '''
        if timeout is None:
            timeout = __class__.default_timeout

        mode = 'r' if self.exists() else 'w'  # w will ensure creation
        if exclusive:
            mode += '+'  # r+ is for reading and writing but without truncation

        self.fp = open(self.file_name, mode)
        self.exclusive = exclusive
        lock_type = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH

        if timeout == 0:  # try non-blocking lock (but also with timeout to make it more safe)
            lock_type |= fcntl.LOCK_NB
            timeout = 1

        try:
            with timeoutcontext.timeout(timeout):
                fcntl.flock(self.fp, lock_type)
        except (IOError, OSError, TimeoutError):
            self.fp.close()
            self.fp = None
            return False

        return True

    def close(self) -> bool:
        '''
        Unlock and close the file. Returns true on success, false if the file is already closed.
        '''
        if self.fp is None:
            return False

        fcntl.flock(self.fp, fcntl.LOCK_UN)
        self.fp.close()
        self.fp = None
        return True

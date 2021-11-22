import datetime
import threading
import time
import traceback
import inspect
import ctypes


class MultipleThreading(threading.Thread):
    '''
    重写单线程run方法，添加获取返回值的方法
    '''
    def __init__(self, func, args=(), kwargs=None):
        threading.Thread.__init__(self)
        self.func = func
        self.args = args
        if kwargs is None:
            kwargs = {}
        self.kwargs = kwargs
        self.errCode = 0
        self.errMessage = ''
        self.result = None

    def run(self):
        """重写run()方法"""
        subThreadName = self.func.__name__ + " - " + str(threading.currentThread().getName()) + " - " + str(
            threading.currentThread().ident)
        time_start = datetime.datetime.now()
        print('func_name is: {},start at {}\r'.format(subThreadName, time_start))
        # self.result = self.func(*self.args, **self.kwargs)
        try:
            self.result = self.func(*self.args, **self.kwargs)
        except:
            self.errCode = 1
            self.errMessage = traceback.print_exc()
        time_stop = datetime.datetime.now()
        print('func_name is: {},stop at {},cost {}\r'.format(subThreadName, time_stop, time_stop-time_start))
        return self.result

    def get_result(self):
        """
        获取线程返回值
        :return:
        """
        try:
            return self.result
        except Exception:
            return None


class ParallelOperation:
    """
    简化多线程方法，减少代码循环，增加线程集add、start、join、stop、clear、result方法
    """
    def __init__(self):
        self.thread_list = []
        self.thread_result = []

    def add(self, func, args=(), **kwargs):
        """
        添加线程到线程集
        :param func:函数名
        :param args:函数实参元组
        :param kwargs:函数补充参数
        :return:
        """
        t = MultipleThreading(func, args, kwargs)
        self.thread_list.append(t)
        return self.thread_list

    def start(self):
        """
        启动多线程
        :return:
        """
        for thread in self.thread_list:
            try:
                thread.start()
            except Exception:
                continue
        # for thread in self.thread_list:
        #     try:
        #         thread.join()
        #     except Exception:
        #         continue
        #     print(thread.errCode)
        #     if thread.errCode == 1:
        #         print(thread.errMessage)
        #         raise Exception('线程挂了吧？')

    def _async_raise(self, id, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(id)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def stop(self):
        """停止多线程"""
        for thread in self.thread_list:
            try:
                if thread.is_alive():
                    self._async_raise(thread.ident, SystemExit)
            except Exception:
                continue


    def join(self):
        """等待线程集中所有线程结束"""
        for thread in self.thread_list:
            try:
                thread.join()
            except:
                self._async_raise(thread.ident, SystemExit)
                continue

    def clear(self):
        """清理线程集"""
        self.thread_list = []
        self.thread_result = []

    def result(self):
        """获取线程集中个线程的返回值"""
        for thread in self.thread_list:
            try:
                result = thread.get_result()
                self.thread_result.append(result)
            except:
                continue
        return self.thread_result

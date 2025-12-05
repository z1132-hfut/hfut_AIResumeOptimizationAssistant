"""
客户端操作类
"""
import json
from typing import Any

import redis
from logger import get_logger

log = get_logger(__name__)


class RedisClient(object):
    """
    用于执行redis数据库操作
    """
    def __init__(self, queue_name = "Queue_RO",host='localhost', port=6379, db=0, password=None):
        self.queue_name = queue_name
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,  # 自动解码为字符串
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            if self.client.ping():
                log.info(f"Redis连接成功 - {host}:{port} DB:{db}")

        except Exception as e:
            log.error(f"Redis连接失败: {e}")
            raise


    def pushQueue_RO(self, task_data:dict)->bool:
        """
        将简历打分+优化请求加入消息队列，发布订阅信息。
        :return:加入是否成功。
        """
        try:
            # 序列化任务数据
            task_str = json.dumps(task_data, ensure_ascii=False)
            result = self.client.lpush(self.queue_name, task_str)
            log.info(f"任务推送成功 - 队列: {self.queue_name}")
            # log.info(f"任务推送成功 - 队列: {self.queue_name}, 数据: {task_data}")

            return bool(result)
        except Exception as e:
            log.error(f"任务推送失败{e}")
            return False


    def popQueue_RO(self, timeout: int = 0)->Any:
        """
        从消息队列中获取简历打分+优化请求
        :return:task_data。消息队列里的信息
        """
        try:
            result = self.client.brpop([self.queue_name],timeout=timeout)
            if result:
                log.debug(f"任务获取成功 - 队列: {self.queue_name}")
                return result
            return None

        except Exception as e:
            log.error(f"任务获取失败{e}")


    def input_res(self, task_id: str, res_data: str) -> bool:
        """
        将处理好的简历打分任务结果以字符串形式存入redis
        :param task_id: 任务id
        :param res_data: 任务处理结果
        :return: 是否成功
        """
        try:
            # 使用任务ID作为键，存储结果数据
            # 设置过期时间为24小时（86400秒），避免数据长期堆积
            result = self.client.setex(
                f"res_result:{task_id}",
                86400,
                res_data
            )
            if result:
                log.info(f"结果存储成功 - 任务ID: {task_id}")
                return True
            else:
                log.error(f"结果存储失败 - 任务ID: {task_id}")
                return False
        except Exception as e:
            log.error(f"结果存储异常 - 任务ID: {task_id}, 错误: {e}")
            return False


    def get_res(self, task_id: str) -> str:
        """
        使用id将处理结果取出
        :param task_id: 任务id
        :return: 任务处理结果
        """
        try:
            result = self.client.get(f"res_result:{task_id}")
            if result is not None:
                log.info(f"结果获取成功 - 任务ID: {task_id}")
                return str(result)
            else:
                log.warning(f"结果不存在 - 任务ID: {task_id}")
                return "暂无"
        except Exception as e:
            log.error(f"结果获取异常 - 任务ID: {task_id}, 错误: {e}")
            return "暂无"


    def get_queue_length(self) -> int:
        """获取队列长度"""
        try:
            return self.client.llen(self.queue_name)
        except Exception as e:
            log.error(f"获取队列长度失败: {e}")
            return 0



if __name__ == "__main__":
    a = RedisClient()
    a.input_res("task1","task1的处理结果")
    a.get_res("task1")
    # 测试功能：
    # resume_optimization_queue = RedisClient("Queue_RO")
    # task_info = {"pdf全部文本": "pdf_text", "岗位名称": "数据分析师", "岗位描述": "job_description", "其他信息": "more_info",
    #              "用户备注": "user_request"}
    #
    # task_queue = {"task_id": "task_id", "task_info": task_info, "text": "task_texts[0][0]",
    #               "task_type": "task_texts[0][1]"}
    # task_id = "t"
    # a = 1
    # while a<=2:
    #     task_queue["task_id"] = task_id+"_"+str(a)
    #     resume_optimization_queue.pushQueue_RO(task_queue)
    #     a+=1

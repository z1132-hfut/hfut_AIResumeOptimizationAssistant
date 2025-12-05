"""
运行：1、uvicorn main:app --reload --host 0.0.0.0  2、运行订阅者
进入网页：http://127.0.0.1:8000/docs
"""
import io
import threading
from datetime import datetime
from urllib.parse import unquote
from typing import Optional
import pdfplumber
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import time

from LLMs.deepseekUser import deepseekUser
from LLMs.KimiUser import KimiUser
from logger import get_logger
from redis_client import RedisClient

from fastapi import FastAPI, HTTPException, UploadFile, File, Form

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://10.4.113.20:3000"  # 新增：允许局域网前端IP
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


log = get_logger(__name__)
rc = RedisClient()
deepseek = deepseekUser()
kimi = KimiUser()

class ResumeOptimization(BaseModel):
    """
    简历优化方法的传入模型。分别为：pdf文件，岗位名称，岗位描述，公司名称及其他信息，备注或特殊需求
    """
    file:UploadFile = File(...)
    job_name: Optional[str] = ""
    job_description: Optional[str] = ""
    more_info: Optional[str] = "暂无"
    user_request: Optional[str] = "暂无"


class ResumeOptimization_chat(BaseModel):
    """
    简历优化_聊天方法的传入模型。分别为：历史聊天记录（tokens最大3000），用户提示词，简历优化记录
    """
    history_chat_record: Optional[str] = ""
    user_prompt: Optional[str] = ""
    res_opt_record: Optional[str] = ""
    # more_info: Optional[str] = "暂无"

task_texts = [["简历打分+优化任务",1],["简历打分_聊天",2],["面试题目生成",3],["面试题目生成_聊天",4]]

class TaskIDGenerator:
    def __init__(self):
        self._lock = threading.Lock()
        self.task_counter = 0
        self.current_hour = datetime.now().strftime("%Y%m%d%H")

    def generate_task_id(self) -> str:
        """
        生成任务ID
        格式：年月日时分秒 + 8位数字编号
        8位数字编号每小时重置，达到上限99999999时立即更新
        """

        # 获取当前时间
        now = datetime.now()
        current_time_str = now.strftime("%Y%m%d%H%M%S")
        current_hour_str = now.strftime("%Y%m%d%H")

        # 检查是否需要重置计数器（新小时或达到上限）
        if current_hour_str != self.current_hour or self.task_counter >= 99999999:
            self.task_counter = 0
            self.current_hour = current_hour_str

        # 生成8位数字编号，前面补零
        task_number = str(self.task_counter).zfill(8)
        self.task_counter += 1

        task_id = current_time_str + task_number
        return task_id

task_id_generator = TaskIDGenerator()

@app.post("/resume_optimization")
async def resume_optimization(
        # response_model:ResumeOptimization,
        file:UploadFile = File(...),
        job_name: str = Form("", description="岗位名称"),
        job_description: str = Form("", description="岗位描述"),
        more_info: str = Form("", description="其他信息"),
        user_request: str = Form("", description="用户备注")
):

    log.info(f"{task_texts[0][0]}方法开始运行")

    # file = response_model.files["file"]
    # job_name = response_model.job_name
    # job_description = response_model.job_description
    # more_info = response_model.more_info
    # user_request = response_model.user_request

    # job_name = unquote(job_name)
    # job_description = unquote(job_description)
    # more_info = unquote(more_info)
    # user_request = unquote(user_request)

    log.info("信息接收完成")
    pdf_content = await file.read()

    pdf_text = ""
    try:
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pdf_text += page_text + "\n"
    except Exception as e:
        log.error(f"PDF解析失败: {e}")
        raise HTTPException(status_code=400, detail=f"PDF文件解析失败: {str(e)}")

    if not pdf_text.strip():
        raise HTTPException(status_code=400, detail="无法从PDF中提取文本内容")

    pdf_name = file.filename
    # task_id:str 年月日时分秒+8位数字编号。8位数字编号默认每小时重置（默认00000000），若达到上限（99999999）则立即更新。累加。
    task_id = task_id_generator.generate_task_id()
    log.info("task_id:"+task_id)

    current_date = datetime.now().strftime("%Y-%m-%d")

    # task_info:任务内容
    task_info = {"pdf全部文本":pdf_text+"当前时间："+current_date, "岗位名称":job_name, "岗位描述":job_description, "其他信息":more_info,
                 "用户备注":user_request}
    # log.info("简历名称："+pdf_name+"岗位名称:"+job_name+"岗位描述:"+job_description+"其他信息:"+more_info+"用户备注:"+user_request)

    # text:任务名称
    # task_type:任务类型编号
    task_queue = {"task_id": task_id, "task_info": task_info, "text": task_texts[0][0], "task_type": task_texts[0][1]}
    log.info(f"任务上传成功。任务类型{task_texts[0][0]}。任务类型编号{task_texts[0][1]}")

    result = rc.pushQueue_RO(task_queue)
    if result:
        queue_length = rc.get_queue_length()
        log.info(f"任务{task_texts[0][1]}提交成功 - 任务ID: {task_id}, 队列位置: {queue_length}")
        return {"status": "success", "message": task_id}
    else:
        log.error(f"任务{task_texts[0][1]}提交失败")
        raise HTTPException(status_code=500, detail=f"任务{task_texts[0][1]}提交失败")


@app.post("/get_resume_optimization_result")
async def resume_optimization_chat(
        task_id: str = Form("", description="任务id"),
):
    """
    获取简历优化任务结果
    :param task_id: 任务ID
    :return: 任务处理结果
    """
    if not task_id or not task_id.strip():
        return {"status": "error", "message": "任务ID不能为空"}

    log.info(f"查询任务结果 - 任务ID: {task_id}")

    try:
        # 直接获取任务结果
        result = rc.get_res(task_id)

        # 关键修复：严格判断结果是否有效（非空且不是"暂无"）
        if result and result.strip() and result.strip() != "暂无":
            log.info(f"任务结果获取成功 - 任务ID: {task_id}")
            log.info(f"任务结果获取成功 - 结果： {result[:50]}...")  # 只打印前50字符，避免日志过长
            return {
                "status": "success",
                "message": result,
                "task_id": task_id
            }
        else:
            # 结果为空或"暂无"，表示任务仍在处理中
            log.warning(f"任务未完成或结果未生成 - 任务ID: {task_id}")
            return {
                "status": "processing",
                "message": "任务仍在处理中，请稍后重试",
                "task_id": task_id
            }

    except Exception as e:
        log.error(f"查询任务结果时发生错误 - 任务ID: {task_id}, 错误: {e}")
        if "not found" in str(e).lower() or "不存在" in str(e):
            return {
                "status": "not_found",
                "message": f"任务ID不存在: {task_id}",
                "task_id": task_id
            }
        else:
            return {
                "status": "error",
                "message": f"查询失败: {str(e)}",
                "task_id": task_id
            }

@app.post("/resume_optimization_chat")
async def resume_optimization_chat(
        history_chat_record: str = Form("", description="历史聊天信息"),
        user_prompt: str = Form("", description="用户提示词"),
        res_opt_record: str = Form("", description="简历打分优化任务处理结果"),
):
    log.info("聊天方法开始运行")
    current_date = datetime.now().strftime("%Y-%m-%d")
    log.info(history_chat_record)
    log.info(user_prompt+"当前时间："+current_date)
    log.info(res_opt_record)
    try:
        # res = "聊天内容"
        res = kimi.kimi_resume_optimization_chat(history_chat_record, user_prompt, res_opt_record)
        log.info("聊天方法成功")
        return {"status": "success", "message": res}
    except Exception as e:
        log.info(f"聊天方法失败。{e}")
        return {"status": "error", "message": str(e)}



if __name__ == "__main__":
    import uvicorn
    log.info("启动FastAPI服务...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
"""
使用api调用deepseek模型
"""

import os
from typing import List

from openai import OpenAI
from logger import get_logger

log = get_logger()

class deepseekUser():
    def __init__(self):
        try:
            self.client = OpenAI(
                api_key="sk-bcf086289f754ee78fb28e8afd3e9724",
                base_url="https://api.deepseek.com",
            )
            log.info("deepseek大模型连接成功")
        except Exception as e:
            log.error(f"deepseek大模型连接失败！原因：{e}")

    def deepseek_resume_clean(self, resume:str)->str:
        """
        该方法的主要作用是清洗简历内容，去除用户敏感信息
        :param resume: 简历文本
        :return: 清洗后的简历文本
        """
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content":
                        f"请严格按照以下要求为用户简历进行内容清洗，去除用户敏感信息"
                        f"清洗要求：将用户的电话号码，邮箱，qq号，住址，微信号等敏感信息去除。用户名称只保留姓氏，名用*代替。年龄保留。"
                        f"返回格式：直接给出并只允许给出清洗后的完整简历文本内容（原封不动的返回除去用户所有敏感信息后的剩余内容）。"
                        f"禁止在回复时在简历文本前后说其他任何话语（如“我明白了”等），不修改清洗后的简历的任何内容。"
                        f"以下为用户简历：{resume}"},
                ],
                stream=False
            )
            log.info("deepseek大模型简历清洗完成")
        except Exception as e:
            log.error(f"deepseek大模型简历清洗失败！原因：{e}")
            return "deepseek大模型简历清洗失败！暂无不包含用户敏感信息的简历文本。"

        return response.choices[0].message.content

    def deepseek_ks_keyword_extract(self, all_text: str) -> List[str]:
        """
        该方法的主要作用是简历内容和关键词提取，用于知识库检索。提取方向如下：
        ["企业类型", "岗位类型", "不同行业招聘能力偏好特征", "学术科研经历", "学科竞赛经历", "社会实践与领导力经历",
        "企业相关实践经历"]
        :param all_text: 全部内容文本
        :return: 关键词列表
        """
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content":
                        f"请严格按照要求为以下文本（包括用户简历，岗位信息，企业信息等内容）进行内容关键语句提取，"
                        f"用于知识库检索。内容提取方向：[企业类型, 岗位类型, 岗位所在行业, 学术科研经历, 学科竞赛经历, "
                        f"社会实践与领导力经历,企业相关实践经历]"
                        f"提取要求：简洁清晰完整。每一个关键语句不包含过多的信息点。一个提取方向可以有多条关键语句。"
                        f"返回格式：直接给出并只允许给出全部相关联的关键词或语句。每条语句间严格用<#>分割。例如：aa。<#>b，b。<#>cc？"
                        f"禁止在回复时在关键词前后说其他任何话语（如“我明白了”等）。"
                        f"内容文本如下：{all_text}"},
                ],
                stream=False
            )
            log.info("deepseek大模型简历关键词提取完成")
        except Exception as e:
            log.error(f"deepseek大模型简历关键词提取失败！原因：{e}")
            return ["企业类型", "岗位类型", "岗位所在行业", "学术科研经历", "学科竞赛经历", "社会实践与领导力经历",
        "企业相关实践经历"]

        return response.choices[0].message.content.split("<#>")

    def deepseek_resume_optimization_chat(self, history_chat_record: str, user_prompt: str, res_opt_record: str)->str:
        """
        该方法主要作用是关于简历打分优化任务的聊天。
        :param history_chat_record:
        :param user_prompt:
        :param res_opt_record:
        :return: 回复
        """
        log.info(history_chat_record)
        log.info(user_prompt)
        log.info(res_opt_record)
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content":
                        f"你是一名认真负责的学生就业规划助手。请结合历史聊天信息，用户的简历打分+优化结果（包括岗位信息，用户简历"
                        f"内容，打分结果及建议等），严格遵守给出的打分结果（如存在），回答用户说的话。"
                        f"如果没有前置信息，请不要随意称呼用户或编造其他虚假信息。如果用户说的话和简历优化无关，请向用户温和地表示自己是简历打分+优化助手，同时专心回复用户给出的内容。"
                        f"##历史聊天信息：{history_chat_record}。##用户的简历打分+优化结果：{res_opt_record}。##用户说的话："
                        f"{user_prompt}"},
                ],
                stream=False
            )
            log.info("deepseek大模型聊天1任务回答完成")
            return response.choices[0].message.content
        except Exception as e:
            log.error(f"deepseek大模型简历优化_聊天任务回答失败！原因：{e}")
            return "deepseek大模型聊天任务回答失败！"
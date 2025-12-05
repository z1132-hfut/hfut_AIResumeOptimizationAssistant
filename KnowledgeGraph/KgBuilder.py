"""
文件格式处理-添加id列
"""
from KnowledgeGraph.KgUser import KgUser

# import pandas as pd
#
# # 替换为你的CSV文件路径（例如："C:/data/input.csv" 或 "/Users/name/data/input.csv"）
# input_path = r"H:\hfut_roa_datas\kg\jobInfo.csv"
# # 替换为输出文件的路径（可与原始文件同名，会覆盖；建议先备份原始文件）
# output_path = r"H:\hfut_roa_datas\kg\jobInfo_id.csv"
#
# # 读取CSV（十万行数据仅需几秒）
# df = pd.read_csv(input_path)
#
# # 在第一列插入主键列"id"，值从1开始递增（1,2,3,...,100000）
# df.insert(0, "id", range(1, len(df) + 1))
#
# # 保存结果（index=False确保不额外生成索引列）
# df.to_csv(output_path, index=False)
#
# print(f"处理完成！已保存到：{output_path}")

if __name__ == "__main__":
    kg = KgUser()
    kg.save_kg_to_txt()



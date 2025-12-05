"""
构建知识库
"""
import uuid
import json
import chromadb
from typing import List, Dict, Any
import os
from logger import get_logger

log = get_logger()


# 持久化客户端
client = chromadb.PersistentClient(path="./chroma_db")

# 创建或获取集合
try:
    collection = client.get_collection(name="res_opt_documents")
except Exception as e:
    if "not found" in str(e).lower() or "does not exist" in str(e).lower():
        collection = client.create_collection(name="res_opt_documents")
    else:
        raise e

class KsBuilder:
    def __init__(self):
        pass

    def save_txt_to_db(self, file_path: str):
        """
        将.txt文件存入数据库
        Args:
            file_path: txt文件路径，文件内容应为JSON数组格式
        """
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析JSON
            data = json.loads(content)

            if not isinstance(data, list):
                log.error(f"文件 {file_path} 内容不是JSON数组格式")
                return

            # 准备批量插入数据
            documents = []
            metadatas = []
            ids = []

            for i, item in enumerate(data):
                if isinstance(item, dict):
                    # 提取文本和元数据
                    text = item.get("text", "")
                    metadata = item.get("metadata", {})

                    # 添加文件名作为元数据的一部分
                    if not isinstance(metadata, dict):
                        metadata = {}

                    # 添加文件名信息
                    metadata["source_file"] = os.path.basename(file_path)

                    # 处理元数据：将所有列表类型的值转换为字符串
                    processed_metadata = self._process_metadata_for_chromadb(metadata)

                    # 生成唯一ID
                    doc_id = f"{os.path.basename(file_path)}_{i}_{str(uuid.uuid4())[:8]}"

                    documents.append(text)
                    metadatas.append(processed_metadata)
                    ids.append(doc_id)

            # 批量插入数据
            if documents:
                # 删除已存在的相同源文件的文档（避免重复）
                existing_docs = collection.get(
                    where={"source_file": os.path.basename(file_path)}
                )

                if existing_docs and existing_docs['ids']:
                    log.info(f"删除 {len(existing_docs['ids'])} 个来自 {file_path} 的旧文档")
                    collection.delete(ids=existing_docs['ids'])

                # 插入新文档
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )

                log.info(f"成功从 {file_path} 添加 {len(documents)} 个文档到数据库")
            else:
                log.warning(f"文件 {file_path} 中没有有效的数据条目")

        except json.JSONDecodeError as e:
            log.error(f"文件 {file_path} JSON解析错误: {e}")
        except Exception as e:
            log.error(f"处理文件 {file_path} 时发生错误: {e}")

    def _process_metadata_for_chromadb(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理元数据，将不支持的类型转换为ChromaDB支持的格式
        Args:
            metadata: 原始元数据字典
        Returns:
            处理后的元数据字典
        """
        processed = {}

        for key, value in metadata.items():
            # 处理列表类型：转换为逗号分隔的字符串
            if isinstance(value, list):
                processed[key] = ", ".join(str(item) for item in value)
            # 处理字典类型：转换为JSON字符串
            elif isinstance(value, dict):
                processed[key] = json.dumps(value, ensure_ascii=False)
            # 处理嵌套结构：递归处理
            elif isinstance(value, (list, dict)):
                # 对于复杂的嵌套结构，转换为JSON字符串
                processed[key] = json.dumps(value, ensure_ascii=False)
            # 处理基本类型：保持原样
            elif isinstance(value, (str, int, float, bool)) or value is None:
                processed[key] = value
            # 处理其他类型：转换为字符串
            else:
                processed[key] = str(value)

        return processed

    def _parse_metadata_from_chromadb(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        从ChromaDB元数据中解析原始格式
        Args:
            metadata: ChromaDB返回的元数据字典
        Returns:
            解析后的元数据字典
        """
        parsed = {}

        for key, value in metadata.items():
            # 尝试解析可能被转换为JSON字符串的值
            if isinstance(value, str):
                # 检查是否是JSON字符串
                if value.startswith('[') and value.endswith(']'):
                    try:
                        parsed[key] = json.loads(value)
                        continue
                    except:
                        pass
                elif value.startswith('{') and value.endswith('}'):
                    try:
                        parsed[key] = json.loads(value)
                        continue
                    except:
                        pass
                # 检查是否是逗号分隔的列表字符串
                elif ',' in value and '[' not in value:
                    items = [item.strip() for item in value.split(',')]
                    # 如果所有项都是简单字符串，保留为列表
                    if all(not item.startswith('{') for item in items):
                        parsed[key] = items
                        continue

            # 保持原样
            parsed[key] = value

        return parsed


# 使用示例
if __name__ == "__main__":
    ks = KsBuilder()

    folder_path = "ks_data"

    filenames = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) and filename.endswith('.txt'):
            filenames.append(file_path)

    for file_path in filenames:
        log.info(f"处理文件: {file_path}")
        ks.save_txt_to_db(file_path)

    log.info("所有文件处理完成")
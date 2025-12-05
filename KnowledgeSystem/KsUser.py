"""
使用知识库
"""

import chromadb
from typing import List, Dict, Any, Tuple, Optional
import re
from logger import get_logger

log = get_logger()


class KsUser:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_collection(name="res_opt_documents")

        # 扩展的关键词到分类映射表
        self.keyword_to_category = {
            # 企业类型
            "国企": "国有企业（央企/大型地方国企）",
            "国有企业": "国有企业（央企/大型地方国企）",
            "央企": "国有企业（央企/大型地方国企）",
            "地方国企": "国有企业（央企/大型地方国企）",
            "国有": "国有企业（央企/大型地方国企）",
            "中央企业": "国有企业（央企/大型地方国企）",

            "私企": "成熟私营企业/互联网大厂",
            "私营": "成熟私营企业/互联网大厂",
            "民营企业": "成熟私营企业/互联网大厂",
            "互联网": "成熟私营企业/互联网大厂",
            "大厂": "成熟私营企业/互联网大厂",
            "科技公司": "成熟私营企业/互联网大厂",

            "外企": "外资企业（跨国公司）",
            "外资": "外资企业（跨国公司）",
            "跨国公司": "外资企业（跨国公司）",
            "mnc": "外资企业（跨国公司）",

            "创业": "初创企业/高成长性科技公司",
            "初创": "初创企业/高成长性科技公司",
            "独角兽": "初创企业/高成长性科技公司",

            "政府": "政府机构/事业单位",
            "事业单位": "政府机构/事业单位",
            "公务员": "政府机构/事业单位",

            # 岗位职能
            "研发": "研发/工程/技术类",
            "技术": "研发/工程/技术类",
            "工程": "研发/工程/技术类",
            "程序员": "研发/工程/技术类",
            "开发": "研发/工程/技术类",
            "工程师": "研发/工程/技术类",

            "产品": "产品/运营/增长类",
            "运营": "产品/运营/增长类",
            "增长": "产品/运营/增长类",

            "数据": "数据科学/分析师",
            "数据分析": "数据科学/分析师",
            "数据科学": "数据科学/分析师",

            "金融": "金融/投资/风控类",
            "投资": "金融/投资/风控类",
            "风控": "金融/投资/风控类",
            "银行": "金融/投资/风控类",
            "证券": "金融/投资/风控类",

            "咨询": "咨询/战略/商业分析",
            "战略": "咨询/战略/商业分析",
            "商业分析": "咨询/战略/商业分析",

            "供应链": "供应链/制造/采购",
            "制造": "供应链/制造/采购",
            "采购": "供应链/制造/采购",
            "生产": "供应链/制造/采购",

            # 学术经历
            "论文": "学术论文发表",
            "学术论文": "学术论文发表",
            "sci": "学术论文发表",
            "期刊": "学术论文发表",

            "毕业设计": "毕业设计/毕业论文",
            "毕业论文": "毕业设计/毕业论文",

            "专利": "专利与软件著作权",
            "发明专利": "专利与软件著作权",
            "软件著作权": "专利与软件著作权",

            "竞赛": "技术算法类竞赛",
            "比赛": "技术算法类竞赛",
            "acm": "技术算法类竞赛",
            "kaggle": "技术算法类竞赛",
            "挑战杯": "综合类/创新创业竞赛",  # 新增
            "大创": "综合类/创新创业竞赛",    # 新增

            "科研": "导师纵向科研项目",
            "科研项目": "导师纵向科研项目",
            "国家自然科学基金": "导师纵向科研项目",

            "实验室": "实验室/课题组日常科研",
            "课题组": "实验室/课题组日常科研",

            "实习": "知名企业核心岗位实习",

            "学生会": "学生会/研究生会核心任职",
            "社团": "社团/协会创办或主导",

            # 行业
            "医药": "医药/生物技术/医疗器械",
            "医疗": "医药/生物技术/医疗器械",
            "生物": "医药/生物技术/医疗器械",
            "医疗器械": "医药/生物技术/医疗器械",

            "制造": "新能源/高端制造/硬科技",
            "新能源": "新能源/高端制造/硬科技",
            "硬科技": "新能源/高端制造/硬科技",
            "半导体": "新能源/高端制造/硬科技",
            "传统制造业": "新能源/高端制造/硬科技",  # 新增

            "快消": "快速消费品/零售/奢侈品",
            "消费品": "快速消费品/零售/奢侈品",
            "零售": "快速消费品/零售/奢侈品",
            "奢侈品": "快速消费品/零售/奢侈品",

            # 其他常见关键词
            "数学竞赛": "专业技能/学科类竞赛",  # 新增
            "一等奖": "专业技能/学科类竞赛",    # 新增
        }

    def search_similar_text(self, query_texts: List[str], n_results: int = 2) -> List[str]:
        """
        对批量名词/关键词进行相似性搜索，返回相关描述
        """
        try:
            if not query_texts:
                return []

            all_results = []

            for keyword in query_texts:
                keyword = keyword.strip()
                if not keyword:
                    continue

                keyword_results = self._search_single_keyword(keyword, n_results)
                all_results.extend(keyword_results)

            return all_results

        except Exception as e:
            log.error(f"搜索出错: {e}")
            return []

    def _search_single_keyword(self, keyword: str, n_results: int) -> List[str]:
        """
        搜索单个关键词
        """
        # 1. 首先检查是否是映射的关键词
        if keyword in self.keyword_to_category:
            category = self.keyword_to_category[keyword]
            results = self._search_by_exact_category(category, n_results)
            if results:
                return self._format_keyword_results(keyword, results, "分类映射")

        # 2. 尝试模糊匹配分类
        category_results = self._search_by_fuzzy_category(keyword, n_results)
        if category_results:
            return self._format_keyword_results(keyword, category_results, "分类匹配")

        # 3. 最后尝试相似性搜索（提高阈值）
        similarity_results = self._search_by_high_quality_similarity(keyword, n_results)
        if similarity_results:
            return self._format_keyword_results(keyword, similarity_results, "相似性搜索")

        # 4. 没有找到结果
        return [f"关键词 '{keyword}'：未找到相关描述"]

    def _search_by_exact_category(self, category: str, n_results: int) -> List[Tuple[str, Dict]]:
        """
        根据精确分类搜索
        """
        try:
            docs = self.collection.get(
                where={"分类": category},
                limit=n_results
            )

            return self._extract_clean_results(docs)
        except Exception as e:
            log.debug(f"精确分类搜索失败: {e}")
            return []

    def _search_by_fuzzy_category(self, keyword: str, n_results: int) -> List[Tuple[str, Dict]]:
        """
        模糊匹配分类
        """
        try:
            # 获取所有分类
            all_docs = self.collection.get()

            matched_docs = []
            seen_texts = set()

            for doc, metadata in zip(all_docs['documents'], all_docs['metadatas']):
                if not isinstance(metadata, dict):
                    continue

                # 检查分类、标签、维度等字段
                category = metadata.get('分类', '')
                tags = metadata.get('标签', '')
                dimension = metadata.get('维度', '')

                # 检查关键词是否出现在这些字段中
                search_fields = [category, tags, dimension]
                for field in search_fields:
                    if isinstance(field, str) and keyword in field:
                        # 提取干净的文本
                        clean_text = self._extract_clean_content(doc, keyword)
                        if clean_text and clean_text not in seen_texts:
                            matched_docs.append((clean_text, metadata))
                            seen_texts.add(clean_text)
                            break

                if len(matched_docs) >= n_results:
                    break

            return matched_docs
        except Exception as e:
            log.debug(f"模糊分类搜索失败: {e}")
            return []

    def _search_by_high_quality_similarity(self, keyword: str, n_results: int) -> List[Tuple[str, Dict]]:
        """
        高质量相似性搜索（提高阈值）
        """
        try:
            # 使用更高的n_results进行搜索，然后严格过滤
            results = self.collection.query(
                query_texts=[keyword],
                n_results=n_results * 5,  # 搜索更多结果以便筛选
                include=["documents", "metadatas", "distances"]
            )

            if not results['documents'] or not results['documents'][0]:
                return []

            high_quality_results = []
            seen_texts = set()

            docs = results['documents'][0]
            metadatas = results['metadatas'][0] if results['metadatas'] else []
            distances = results['distances'][0] if results['distances'] else []

            for doc, metadata, distance in zip(docs, metadatas, distances):
                # 计算相似度
                similarity = 1.0 - distance if distance <= 1.0 else 1.0 / (1.0 + distance)

                # 设置高阈值（0.5）
                if similarity < 0.5:
                    continue

                # 提取干净的文本内容
                clean_text = self._extract_clean_content(doc, keyword)
                if not clean_text or len(clean_text) < 20:  # 太短的文本质量不高
                    continue

                # 检查文本质量（避免提取到元数据）
                if self._is_low_quality_text(clean_text):
                    continue

                # 去重
                text_hash = hash(clean_text[:100])  # 使用前100个字符的hash作为去重依据
                if text_hash in seen_texts:
                    continue

                high_quality_results.append((clean_text, metadata))
                seen_texts.add(text_hash)

                if len(high_quality_results) >= n_results:
                    break

            return high_quality_results

        except Exception as e:
            log.debug(f"高质量相似性搜索失败: {e}")
            return []

    def _extract_clean_results(self, docs_result) -> List[Tuple[str, Dict]]:
        """
        从查询结果中提取干净的内容
        """
        results = []
        if not docs_result or not docs_result['documents']:
            return results

        for doc, metadata in zip(docs_result['documents'], docs_result['metadatas']):
            # 提取文档的核心内容（去除元数据和格式化信息）
            clean_text = self._get_document_core_content(doc)
            if clean_text:
                results.append((clean_text, metadata))

        return results

    def _extract_clean_content(self, document: str, keyword: str = "") -> str:
        """
        提取干净的文档内容
        """
        if not document:
            return ""

        # 1. 获取核心内容
        core_content = self._get_document_core_content(document)
        if not core_content:
            return ""

        # 2. 如果有关键词，优先提取包含关键词的部分
        if keyword:
            sentences = re.split(r'[。！？；\n]', core_content)
            keyword_sentences = []

            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and keyword in sentence:
                    clean_sentence = self._clean_text_fragment(sentence)
                    if clean_sentence:
                        keyword_sentences.append(clean_sentence)

            if keyword_sentences:
                # 返回前2个包含关键词的句子
                return " ".join(keyword_sentences[:2])

        # 3. 如果没有关键词或没找到包含关键词的句子，返回开头部分
        return self._clean_text_fragment(core_content[:200])

    def _get_document_core_content(self, document: str) -> str:
        """
        获取文档的核心内容（去除元数据、标签等）
        """
        if not document:
            return ""

        # 清理常见的元数据格式
        lines = document.split('\n')
        content_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 跳过明显是元数据的行
            if self._is_metadata_line(line):
                continue

            # 跳过过短或无意义的行
            if len(line) < 10 and not any(char in line for char in ['、', '，', '。']):
                continue

            content_lines.append(line)

        # 合并内容
        core_content = " ".join(content_lines)

        # 进一步清理
        core_content = re.sub(r'\s+', ' ', core_content)
        core_content = re.sub(r'\[.*?\]', '', core_content)  # 移除括号内容
        core_content = re.sub(r'\{.*?\}', '', core_content)  # 移除大括号内容

        return core_content.strip()

    def _is_metadata_line(self, line: str) -> bool:
        """
        判断一行是否是元数据
        """
        # 常见的元数据模式
        metadata_patterns = [
            r'^[0-9]+\.[0-9]+',  # 数字.数字
            r'^[①②③④⑤]',       # 带圈数字
            r'^[一二三四五六七八九十]、',  # 中文数字
            r'^tags?:',           # tags: 标签
            r'^metadata:',        # metadata:
            r'^维度:',            # 维度:
            r'^分类:',            # 分类:
            r'^标签:',            # 标签:
            r'^排版样式',         # 排版样式
            r'^项目包装',         # 项目包装
            r'^内容表达优化',     # 内容表达优化
        ]

        line_lower = line.lower()
        for pattern in metadata_patterns:
            if re.match(pattern, line_lower):
                return True

        return False

    def _is_low_quality_text(self, text: str) -> bool:
        """
        判断文本是否是低质量的
        """
        if len(text) < 20:
            return True

        # 检查是否包含常见的不相关内容
        low_quality_indicators = [
            '排版样式',
            '项目包装',
            '内容表达优化',
            '参与度低',
            '一、',
            '二、',
            '三、',
            '四、',
        ]

        for indicator in low_quality_indicators:
            if indicator in text:
                return True

        return False

    def _clean_text_fragment(self, text: str, max_length: int = 150) -> str:
        """
        清理文本片段
        """
        if not text:
            return ""

        # 清理空白字符
        text = re.sub(r'\s+', ' ', text).strip()

        # 截断到合适长度
        if len(text) > max_length:
            # 尝试在句子边界处截断
            end_pos = text.rfind('。', 0, max_length)
            if end_pos > max_length // 2:
                text = text[:end_pos+1]
            else:
                text = text[:max_length-3] + "..."

        return text

    def _format_keyword_results(self, keyword: str, results: List[Tuple[str, Dict]], source: str) -> List[str]:
        """
        格式化关键词搜索结果
        """
        if not results:
            return []

        formatted = []
        formatted.append(f"【{keyword}】")

        for i, (text, metadata) in enumerate(results, 1):
            # 获取分类
            category = ""
            if isinstance(metadata, dict):
                category = metadata.get('分类', '')

            # 构建结果行
            if category:
                result_line = f"  {i}. [{category}] {text}"
            else:
                result_line = f"  {i}. {text}"

            formatted.append(result_line)

        return formatted


# 使用示例
if __name__ == "__main__":
    ks = KsUser()

    print("关键词批量搜索测试")
    print("=" * 60)

    # 测试关键词
    test_keywords = [
        # "国有企业",
        # "论文",
        # "互联网",
        # "研发",
        # "专利",
        # "医药",
        # "快消",
        "传统制造业",
        "安徽省龙头企业",
        "挑战杯",
        "大创",
        "志愿者",
        "奖学金",
        "数学竞赛一等奖"
    ]

    results = ks.search_similar_text(test_keywords, n_results=2)

    # 输出结果
    for result in results:
        if result.startswith("【"):
            print()
            print(result)
        elif "未找到相关描述" in result:
            print(f"\n{result}")
        else:
            print(result)

    print("\n" + "=" * 60)
    print("测试完成")
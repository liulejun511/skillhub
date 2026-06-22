"""memoket 异常类型。

把失败语义显式化：解析层只负责「结构性」错误（frontmatter/正文/YAML），
逻辑性缺失（缺 name/description 等必填字段）由校验层（validate_*）报告。
"""


class MemoketError(Exception):
    """所有 memoket 异常的基类。"""


class SkillNotFoundError(MemoketError):
    """目标路径下找不到 SKILL.md。"""


class FrontmatterError(MemoketError):
    """frontmatter 结构性错误的基类。"""


class MissingFrontmatterError(FrontmatterError):
    """文件未以 YAML frontmatter（开头的 `---`）起始。"""


class MalformedFrontmatterError(FrontmatterError):
    """frontmatter 缺少闭合 `---`、YAML 解析失败、或不是键值映射。"""


class EmptyBodyError(MemoketError):
    """frontmatter 之后的 Markdown 正文为空。"""


class ConflictError(MemoketError):
    """安装/写入时与既有技能冲突（如重名）。"""


class MissingFieldError(MemoketError):
    """构建时缺少目标适配器所需的扩展字段。"""

from pydantic import BaseModel


class Text(BaseModel):
    """普通文本信息,可以实现加法"""
    content: str
    type: str = "Text"

    def __add__(self, other):
        if isinstance(other, Text):
            return Text(content=self.content + other.content)
        else:
            return NotImplemented

    def __str__(self):
        return self.content


class SuggestRely(BaseModel):
    """建议回复信息"""
    content: str
    type: str = "SuggestRely"

    def __str__(self):
        return self.content


class ChatTiTleUpdate(BaseModel):
    """聊天窗口标题变更信息"""
    content: str
    type: str = "ChatTiTleUpdate"

    def __str__(self):
        return self.content


class ChatCodeUpdate(BaseModel):
    """新生成的chat的chat code"""
    content: str
    type: str = "ChatCodeUpdate"

    def __str__(self):
        return str(self.content)

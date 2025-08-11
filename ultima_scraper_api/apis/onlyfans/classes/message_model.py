from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from ultima_scraper_api.apis.onlyfans import SiteContent

if TYPE_CHECKING:
    from ultima_scraper_api.apis.onlyfans.classes.user_model import UserModel


class MessageModel(SiteContent):
    def __init__(
        self, option: dict[str, Any], user: UserModel
    ) -> None:
        # Determine the author based on fromUser
        author = user.get_authed().resolve_user(option.get("fromUser", {}))
        self.user = user
        SiteContent.__init__(self, option, author)
        
        # Basic message properties
        self.responseType: Optional[str] = option.get("responseType", "message")
        self.text: str = option.get("text", "")
        self.lockedText: Optional[bool] = option.get("lockedText")
        self.isFree: Optional[bool] = option.get("isFree", True)
        self.price: int | None = option.get("price", 0)
        self.isMediaReady: Optional[bool] = option.get("isMediaReady", True)
        self.media_count: Optional[int] = option.get("mediaCount", 0)
        self.media: list[Any] = option.get("media", [])
        self.previews: list[dict[str, Any]] = option.get("previews", [])
        self.isTip: Optional[bool] = option.get("isTip", False)
        self.isReportedByMe: Optional[bool] = option.get("isReportedByMe")
        self.fromUser = author
        self.isFromQueue: Optional[bool] = option.get("isFromQueue", False)
        self.queue_id: Optional[int] = option.get("queueId")
        self.canUnsendQueue: Optional[bool] = option.get("canUnsendQueue")
        self.unsendSecondsQueue: Optional[int] = option.get("unsendSecondsQueue")
        self.isOpened: Optional[bool] = option.get("isOpened", True)
        self.isNew: Optional[bool] = option.get("isNew", False)
        
        # Handle datetime
        if "createdAt" in option:
            if isinstance(option["createdAt"], str):
                self.created_at: datetime = datetime.fromisoformat(option["createdAt"].replace('Z', '+00:00'))
            else:
                self.created_at: datetime = datetime.fromtimestamp(option["createdAt"])
        else:
            self.created_at = datetime.now()
            
        self.changedAt: Optional[str] = option.get("changedAt")
        self.cancelSeconds: Optional[int] = option.get("cancelSeconds")
        self.isLiked: Optional[bool] = option.get("isLiked", False)
        self.canPurchase: Optional[bool] = option.get("canPurchase", False)
        self.canPurchaseReason: Optional[str] = option.get("canPurchaseReason")
        self.canReport: Optional[bool] = option.get("canReport", True)
        
        # OnlyFans specific
        self.is_from_queue: Optional[bool] = option.get("isFromQueue", False)
        self.giphy: Optional[dict[str, Any]] = option.get("giphy")
        self.media: list[dict[str, Any]] = option.get("media", [])
        
        # Set canView for media items
        for media_item in self.media:
            if "canView" not in media_item:
                media_item["canView"] = self.isMediaReady and (self.isFree or self.price == 0)

    def get_author(self):
        return self.author

    def get_receiver(self):
        receiver = (
            self.author.get_authed() if self.author.id == self.user.id else self.user
        )
        return receiver

    def is_mass_message(self) -> bool:
        """Check if this is a mass message"""
        return self.isFromQueue or self.queue_id is not None

    async def buy_ppv(self):
        """Purchase pay-per-view message content"""
        if not self.canPurchase or self.price == 0:
            return False
        
        # Implement PPV purchase logic here
        # This would call the appropriate API endpoint
        pass

    def __repr__(self) -> str:
        return f"MessageModel(id={self.id}, text='{self.text[:30]}...', price={self.price})"
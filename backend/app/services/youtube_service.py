import logging
from typing import Optional, Dict, Any, List

try:
    from googleapiclient.discovery import build
except ImportError:
    build = None

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

from app.core.config import settings

logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        self.youtube = None
        if self.api_key and build:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key, cache_discovery=False)
            except Exception as e:
                logger.error(f"Failed to initialize YouTube client: {e}")

    async def audit_company_youtube(self, company_name: str) -> Dict[str, Any]:
        """
        Main entry point for auditing a company's YouTube presence.
        Returns channel info, recent videos, and transcripts.
        """
        if not self.youtube:
            return {"error": "YouTube API key not configured or client failed to initialize."}

        try:
            # 1. Search for the channel
            channel_id = self._search_channel(company_name)
            if not channel_id:
                return {"error": "No official YouTube channel found."}

            # 2. Get channel stats
            channel_stats = self._get_channel_stats(channel_id)

            # 3. Get recent videos
            videos = self._get_recent_videos(channel_id, max_results=3)

            # 4. Extract transcripts for the videos
            for video in videos:
                video["transcript"] = self._get_video_transcript(video["video_id"])

            return {
                "channel_id": channel_id,
                "stats": channel_stats,
                "recent_videos": videos
            }
        except Exception as e:
            logger.error(f"Error auditing YouTube for {company_name}: {e}")
            return {"error": str(e)}

    def _search_channel(self, company_name: str) -> Optional[str]:
        request = self.youtube.search().list(
            q=f"{company_name} official channel",
            part="snippet",
            type="channel",
            maxResults=1
        )
        response = request.execute()
        items = response.get("items", [])
        if not items:
            return None
        return items[0]["snippet"]["channelId"]

    def _get_channel_stats(self, channel_id: str) -> Dict[str, Any]:
        request = self.youtube.channels().list(
            part="statistics,snippet",
            id=channel_id
        )
        response = request.execute()
        items = response.get("items", [])
        if not items:
            return {}
        
        stats = items[0].get("statistics", {})
        snippet = items[0].get("snippet", {})
        return {
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "subscriber_count": stats.get("subscriberCount"),
            "video_count": stats.get("videoCount"),
            "view_count": stats.get("viewCount")
        }

    def _get_recent_videos(self, channel_id: str, max_results: int = 3) -> List[Dict[str, Any]]:
        request = self.youtube.search().list(
            part="snippet",
            channelId=channel_id,
            order="date",
            type="video",
            maxResults=max_results
        )
        response = request.execute()
        videos = []
        for item in response.get("items", []):
            videos.append({
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"],
                "published_at": item["snippet"]["publishedAt"]
            })
        return videos

    def _get_video_transcript(self, video_id: str) -> str:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['de', 'en'])
            # Join the text parts, limit to first 1000 chars to save token space
            full_text = " ".join([t["text"] for t in transcript_list])
            return full_text[:1000] + ("..." if len(full_text) > 1000 else "")
        except Exception as e:
            logger.warning(f"Could not fetch transcript for {video_id}: {e}")
            return "No transcript available."

youtube_service = YouTubeService()

import aiohttp
import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("ghl_mcp_client")

class GHLMCPClient:
    """Client for communicating with GoHighLevel MCP server."""
    
    def __init__(self, mcp_server_url: str):
        self.base_url = mcp_server_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        # Calendar mappings based on conversation context
        self.calendar_mappings = {
            "jewelry": os.getenv("GHL_CALENDAR_JEWELLER_ID", "CuOcD0x88h7NPvfub9"),
            "audit": os.getenv("GHL_CALENDAR_AUDIT_ID", "GHPSw9oQ8DDQJaJVVQbE"),
            "consultation": os.getenv("GHL_CALENDAR_BOOKCALL_ID", "IRCCTTBGxfhK8pRbNfT"),
            "default": os.getenv("GHL_DEFAULT_CALENDAR_ID", "1a2FZj1zqXPbPnrElQD1")
        }
    
    async def create_contact_and_schedule(
        self, 
        name: str, 
        email: str, 
        phone: str,
        notes: str, 
        calendar_id: str, 
        start_time: str
    ) -> Dict[str, Any]:
        """Create contact and schedule appointment via MCP server."""
        
        payload = {
            "tool_name": "create_contact_add_notes_schedule_appointment",
            "arguments": {
                "name": name,
                "email": email, 
                "phone": phone,
                "notes": notes,
                "calendar_id": calendar_id,
                "start_time": start_time
            }
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/mcp/call_tool",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    logger.info(f"✅ GHL MCP successful: Contact created for {name}")
                    return result
        except aiohttp.ClientError as e:
            logger.error(f"❌ GHL MCP client error: {e}")
            return {"error": f"MCP server communication failed: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ GHL MCP unexpected error: {e}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def select_calendar(self, conversation_context: str) -> str:
        """Select appropriate calendar based on conversation context."""
        context_lower = conversation_context.lower()
        
        # Check for specific appointment types (order matters - most specific first)
        if any(word in context_lower for word in ['appraisal', 'audit', 'evaluation', 'assessment', 'appraised']):
            return self.calendar_mappings["audit"]
        elif any(word in context_lower for word in ['consultation', 'design consultation', 'meeting', 'discuss', 'schedule a consultation']):
            return self.calendar_mappings["consultation"]
        elif any(word in context_lower for word in ['jewelry', 'ring', 'necklace', 'bracelet', 'earring', 'custom design']):
            return self.calendar_mappings["jewelry"]
        else:
            return self.calendar_mappings["default"]
    
    def suggest_appointment_time(self, preferred_time: Optional[str] = None) -> str:
        """Suggest an appointment time. Default to next business day at 2 PM if no preference."""
        if preferred_time:
            try:
                # Try to parse user's preferred time
                # This is a simple implementation - you might want more sophisticated parsing
                return preferred_time
            except Exception:
                logger.warning(f"Could not parse preferred time: {preferred_time}")
        
        # Default to next business day at 2 PM
        now = datetime.now()
        next_business_day = now + timedelta(days=1)
        
        # Skip weekends
        while next_business_day.weekday() >= 5:  # Saturday=5, Sunday=6
            next_business_day += timedelta(days=1)
        
        # Set to 2 PM
        suggested_time = next_business_day.replace(hour=14, minute=0, second=0, microsecond=0)
        return suggested_time.isoformat()

class CustomerInfoExtractor:
    """Extract customer information from conversation text."""
    
    @staticmethod
    def extract_contact_info(conversation_text: str) -> Dict[str, Optional[str]]:
        """Extract name, email, and phone from conversation text."""
        import re
        
        # Simple regex patterns - you might want to enhance these
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        
        # Extract email
        email_match = re.search(email_pattern, conversation_text)
        email = email_match.group(0) if email_match else None
        
        # Extract phone
        phone_match = re.search(phone_pattern, conversation_text)
        phone = ''.join(phone_match.groups()) if phone_match else None
        if phone:
            phone = f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
        
        # Name extraction is more complex - for now, we'll leave it to be manually provided
        # You could enhance this with NLP libraries like spaCy
        name = None
        
        return {
            "name": name,
            "email": email,
            "phone": phone
        }
    
    @staticmethod
    def generate_conversation_summary(messages: list, max_length: int = 500) -> str:
        """Generate a concise summary of the conversation for notes."""
        if not messages:
            return "No conversation data available."
        
        # Get last few messages to create summary
        recent_messages = messages[-6:] if len(messages) > 6 else messages
        
        summary_parts = []
        for msg in recent_messages:
            role = "Customer" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")[:100]  # Truncate long messages
            summary_parts.append(f"{role}: {content}")
        
        summary = " | ".join(summary_parts)
        
        # Truncate if too long
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return f"Conversation Summary: {summary}"

class GHLAppointmentScheduler:
    """High-level appointment scheduling interface."""
    
    def __init__(self, mcp_client: GHLMCPClient):
        self.mcp_client = mcp_client
        self.extractor = CustomerInfoExtractor()
    
    async def schedule_from_conversation(
        self,
        conversation_messages: list,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
        preferred_time: Optional[str] = None,
        appointment_type: str = "consultation"
    ) -> Dict[str, Any]:
        """Schedule appointment from conversation data."""
        
        # Validate required information
        if not all([customer_name, customer_email, customer_phone]):
            return {
                "success": False,
                "error": "Missing required customer information (name, email, phone)"
            }
        
        # Generate conversation summary
        conversation_summary = self.extractor.generate_conversation_summary(conversation_messages)
        
        # Select appropriate calendar
        conversation_text = " ".join([msg.get("content", "") for msg in conversation_messages])
        calendar_id = self.mcp_client.select_calendar(conversation_text)
        
        # Suggest appointment time
        appointment_time = self.mcp_client.suggest_appointment_time(preferred_time)
        
        # Create contact and schedule appointment
        result = await self.mcp_client.create_contact_and_schedule(
            name=customer_name,
            email=customer_email,
            phone=customer_phone,
            notes=conversation_summary,
            calendar_id=calendar_id,
            start_time=appointment_time
        )
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"]
            }
        
        return {
            "success": True,
            "result": result,
            "appointment_time": appointment_time,
            "calendar_type": self._get_calendar_type(calendar_id)
        }
    
    def _get_calendar_type(self, calendar_id: str) -> str:
        """Get calendar type description from ID."""
        for cal_type, cal_id in self.mcp_client.calendar_mappings.items():
            if cal_id == calendar_id:
                return cal_type
        return "unknown" 
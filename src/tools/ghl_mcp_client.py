import aiohttp
import json
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger("ghl_mcp_client")

class GHLMCPClient:
    """Client for communicating with GoHighLevel MCP server."""
    
    def __init__(self, mcp_server_url: str):
        self.base_url = mcp_server_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        # Updated calendar mappings with active calendar IDs
        self.calendar_mappings = {
            "demo": "1a2FZj1zqXPbPnrElQD1",           # Demo calendar
            "custom_jewelry": "1c0RCj9LXQr9iDQaDTn9",  # Custom Jewelry Design
            "appraisals": "7pRF2Il5lcRZIMBdSkBx",      # Appraisals  
            "campaign": "CuOcD0x88h7NPvfub9",          # Campaign
            "default": "1a2FZj1zqXPbPnrElQD1"          # Default to demo
        }
        
        # Available MCP tools
        self.available_tools = [
            "get_contact_info",
            "list_opportunities", 
            "trigger_webhook",
            "get_pipeline_info",
            "create_note",
            "search_contacts",
            "get_contact_activities",
            "create_opportunity",
            "create_contact_add_notes_schedule_appointment"
        ]
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generic method to call any MCP tool."""
        if tool_name not in self.available_tools:
            return {"error": f"Tool '{tool_name}' not available. Available tools: {', '.join(self.available_tools)}"}
            
        payload = {
            "tool_name": tool_name,
            "arguments": arguments
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
                    logger.info(f"✅ MCP tool '{tool_name}' executed successfully")
                    return result
        except aiohttp.ClientError as e:
            logger.error(f"❌ MCP client error for {tool_name}: {e}")
            return {"error": f"MCP server communication failed: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ MCP unexpected error for {tool_name}: {e}")
            return {"error": f"Unexpected error: {str(e)}"}
    
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
        
        # Validate calendar ID
        if calendar_id not in self.calendar_mappings.values():
            logger.warning(f"Invalid calendar ID: {calendar_id}. Using default.")
            calendar_id = self.calendar_mappings["default"]
        
        arguments = {
            "name": name,
            "email": email, 
            "phone": phone,
            "notes": notes,
            "calendar_id": calendar_id,
            "start_time": start_time
        }
        
        return await self.call_mcp_tool("create_contact_add_notes_schedule_appointment", arguments)
    
    async def search_contacts(self, email: str = None, phone: str = None) -> Dict[str, Any]:
        """Search for contacts by email or phone."""
        arguments = {}
        if email:
            arguments["email"] = email
        if phone:
            arguments["phone"] = phone
            
        if not arguments:
            return {"error": "Email or phone required for contact search"}
            
        return await self.call_mcp_tool("search_contacts", arguments)
    
    async def get_contact_info(self, contact_id: str) -> Dict[str, Any]:
        """Get detailed contact information by ID."""
        return await self.call_mcp_tool("get_contact_info", {"contact_id": contact_id})
    
    async def create_note(self, contact_id: str, note: str) -> Dict[str, Any]:
        """Add a note to a contact."""
        return await self.call_mcp_tool("create_note", {"contact_id": contact_id, "note": note})
    
    async def create_opportunity(self, contact_id: str, title: str, value: float = None, pipeline_id: str = None) -> Dict[str, Any]:
        """Create a new opportunity for a contact."""
        arguments = {"contact_id": contact_id, "title": title}
        if value is not None:
            arguments["value"] = value
        if pipeline_id:
            arguments["pipeline_id"] = pipeline_id
            
        return await self.call_mcp_tool("create_opportunity", arguments)
    
    async def list_opportunities(self, contact_id: str = None) -> Dict[str, Any]:
        """List opportunities, optionally filtered by contact."""
        arguments = {}
        if contact_id:
            arguments["contact_id"] = contact_id
            
        return await self.call_mcp_tool("list_opportunities", arguments)
    
    async def get_contact_activities(self, contact_id: str) -> Dict[str, Any]:
        """Get activity history for a contact."""
        return await self.call_mcp_tool("get_contact_activities", {"contact_id": contact_id})
    
    async def trigger_webhook(self, webhook_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a custom workflow webhook."""
        arguments = {"webhook_id": webhook_id, "data": data}
        return await self.call_mcp_tool("trigger_webhook", arguments)
    
    async def get_pipeline_info(self, pipeline_id: str = None) -> Dict[str, Any]:
        """Get pipeline/funnel information."""
        arguments = {}
        if pipeline_id:
            arguments["pipeline_id"] = pipeline_id
            
        return await self.call_mcp_tool("get_pipeline_info", arguments)
    
    def select_calendar(self, conversation_context: str) -> str:
        """Select appropriate calendar based on conversation context."""
        context_lower = conversation_context.lower()
        
        # Check for specific appointment types (order matters - most specific first)
        if any(word in context_lower for word in ['appraisal', 'appraise', 'evaluation', 'assessment', 'value', 'worth']):
            return self.calendar_mappings["appraisals"]
        elif any(word in context_lower for word in ['custom', 'design', 'bespoke', 'personalized', 'unique']):
            return self.calendar_mappings["custom_jewelry"]
        elif any(word in context_lower for word in ['campaign', 'promotion', 'special offer', 'deal']):
            return self.calendar_mappings["campaign"]
        else:
            return self.calendar_mappings["demo"]  # Default to demo calendar
    
    def get_calendar_type(self, calendar_id: str) -> str:
        """Get calendar type description from ID."""
        calendar_map = {
            "1a2FZj1zqXPbPnrElQD1": "Demo",
            "1c0RCj9LXQr9iDQaDTn9": "Custom Jewelry Design",
            "7pRF2Il5lcRZIMBdSkBx": "Appraisals",
            "CuOcD0x88h7NPvfub9": "Campaign"
        }
        return calendar_map.get(calendar_id, "Unknown")
    
    def get_available_calendars(self) -> Dict[str, str]:
        """Get all available calendar IDs and their descriptions."""
        return {
            calendar_id: self.get_calendar_type(calendar_id) 
            for calendar_id in self.calendar_mappings.values()
        }
    
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
        
        # Enhanced regex patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        
        # Name extraction patterns - look for common patterns  
        name_patterns = [
            r"my name is ([A-Za-z\s]{2,30}?)(?:\s+and|,|\.|\s*$)",
            r"i'm ([A-Za-z\s]{2,30}?)(?:\s+and|,|\.|\s*$)",
            r"this is ([A-Za-z\s]{2,30}?)(?:\s+and|,|\.|\s*$)",
            r"call me ([A-Za-z\s]{2,30}?)(?:\s+and|,|\.|\s*$)"
        ]
        
        # Extract email
        email_match = re.search(email_pattern, conversation_text)
        email = email_match.group(0) if email_match else None
        
        # Extract phone
        phone_match = re.search(phone_pattern, conversation_text)
        phone = ''.join(phone_match.groups()) if phone_match else None
        if phone:
            phone = f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
        
        # Extract name
        name = None
        for pattern in name_patterns:
            name_match = re.search(pattern, conversation_text.lower())
            if name_match:
                name = name_match.group(1).strip().title()
                break
        
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
            "calendar_type": self.mcp_client.get_calendar_type(calendar_id),
            "calendar_id": calendar_id
        }
    
    async def find_existing_contact(self, email: str = None, phone: str = None) -> Dict[str, Any]:
        """Check if contact already exists in GHL."""
        return await self.mcp_client.search_contacts(email=email, phone=phone)
    
    async def create_follow_up_opportunity(self, contact_id: str, conversation_summary: str) -> Dict[str, Any]:
        """Create a follow-up opportunity based on the conversation."""
        return await self.mcp_client.create_opportunity(
            contact_id=contact_id,
            title="Jewelry Consultation Follow-up",
            value=None  # Will be filled in by sales team
        ) 
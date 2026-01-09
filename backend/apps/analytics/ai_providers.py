"""
AI Provider Manager with Automatic Failover.

Provides a unified interface for multiple AI providers (Claude, OpenAI)
with automatic failover when the primary provider fails.

Usage:
    manager = AIProviderManager(
        primary_provider='anthropic',
        api_keys={'anthropic': 'sk-...', 'openai': 'sk-...'},
        fallback_order=['anthropic', 'openai']
    )
    result = manager.enhance_insights(insights, context)
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    name: str = "base"

    @abstractmethod
    def enhance_insights(
        self,
        insights: list,
        context: dict,
        tool_schema: dict
    ) -> Optional[dict]:
        """
        Generate insight enhancements using the provider's API.

        Args:
            insights: List of insight dictionaries
            context: Comprehensive context for AI analysis
            tool_schema: Tool/function schema for structured output

        Returns:
            Structured enhancement dict or None on failure
        """
        pass

    @abstractmethod
    def analyze_single_insight(
        self,
        insight: dict,
        tool_schema: dict
    ) -> Optional[dict]:
        """
        Analyze a single insight (cost-efficient model).

        Args:
            insight: Single insight dictionary
            tool_schema: Tool/function schema for structured output

        Returns:
            Analysis dict or None on failure
        """
        pass

    @abstractmethod
    def deep_analysis(
        self,
        insight_data: dict,
        context: dict,
        tool_schema: dict
    ) -> Optional[dict]:
        """
        Perform comprehensive deep analysis on an insight.

        Args:
            insight_data: Insight to analyze
            context: Organization/spending context
            tool_schema: Tool/function schema for structured output

        Returns:
            Deep analysis dict or None on failure
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured."""
        pass

    @abstractmethod
    def health_check(self) -> dict:
        """
        Perform a health check on the provider.

        Returns:
            Dict with 'healthy' (bool), 'latency_ms' (int), 'error' (str or None)
        """
        pass


class AnthropicProvider(AIProvider):
    """Claude API provider implementation."""

    name = "anthropic"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        if not self._client and self.api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("anthropic package not installed")
        return self._client

    def is_available(self) -> bool:
        return bool(self.api_key and self.client)

    def health_check(self) -> dict:
        if not self.is_available():
            return {"healthy": False, "latency_ms": 0, "error": "Not configured"}

        import time
        start = time.time()
        try:
            self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}]
            )
            latency = int((time.time() - start) * 1000)
            return {"healthy": True, "latency_ms": latency, "error": None}
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return {"healthy": False, "latency_ms": latency, "error": str(e)}

    def enhance_insights(
        self,
        insights: list,
        context: dict,
        tool_schema: dict
    ) -> Optional[dict]:
        if not self.is_available():
            return None

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                tools=[tool_schema],
                tool_choice={"type": "tool", "name": tool_schema["name"]},
                messages=[{
                    "role": "user",
                    "content": self._build_enhancement_prompt(insights, context)
                }]
            )

            for block in message.content:
                if block.type == "tool_use" and block.name == tool_schema["name"]:
                    result = block.input
                    result['provider'] = 'anthropic'
                    result['generated_at'] = datetime.now().isoformat()
                    return result

            logger.warning("Claude did not return tool_use response")
            return None

        except Exception as e:
            logger.error(f"Anthropic enhancement failed: {e}")
            raise

    def analyze_single_insight(
        self,
        insight: dict,
        tool_schema: dict
    ) -> Optional[dict]:
        if not self.is_available():
            return None

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=500,
                tools=[tool_schema],
                tool_choice={"type": "tool", "name": tool_schema["name"]},
                messages=[{
                    "role": "user",
                    "content": self._build_single_insight_prompt(insight)
                }]
            )

            for block in message.content:
                if block.type == "tool_use" and block.name == tool_schema["name"]:
                    result = block.input
                    result['provider'] = 'anthropic'
                    result['model'] = 'claude-3-5-haiku'
                    result['generated_at'] = datetime.now().isoformat()
                    return result

            return None

        except Exception as e:
            logger.error(f"Anthropic single insight analysis failed: {e}")
            raise

    def deep_analysis(
        self,
        insight_data: dict,
        context: dict,
        tool_schema: dict
    ) -> Optional[dict]:
        if not self.is_available():
            return None

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                tools=[tool_schema],
                tool_choice={"type": "tool", "name": tool_schema["name"]},
                messages=[{
                    "role": "user",
                    "content": self._build_deep_analysis_prompt(insight_data, context)
                }]
            )

            for block in message.content:
                if block.type == "tool_use" and block.name == tool_schema["name"]:
                    result = block.input
                    result['insight_id'] = insight_data.get('id')
                    result['provider'] = 'anthropic'
                    result['model'] = 'claude-sonnet-4'
                    result['generated_at'] = datetime.now().isoformat()
                    return result

            return None

        except Exception as e:
            logger.error(f"Anthropic deep analysis failed: {e}")
            raise

    def _build_enhancement_prompt(self, insights: list, context: dict) -> str:
        return f"""Analyze these procurement insights and provide structured recommendations.

Organization: {context['organization']['name']}

Spending Summary:
- Total YTD Spend: ${context['spending']['total_ytd']:,.2f}
- Supplier Count: {context['spending']['supplier_count']}
- Category Count: {context['spending']['category_count']}
- Transaction Count: {context['spending']['transaction_count']}

Top Categories:
{json.dumps(context['top_categories'], indent=2)}

Top Suppliers:
{json.dumps(context['top_suppliers'], indent=2)}

Current Insights ({len(insights)} total):
{json.dumps(context['insights'], indent=2)}

Provide actionable recommendations prioritized by impact and effort.
Focus on quick wins and high-impact actions that address the identified issues."""

    def _build_single_insight_prompt(self, insight: dict) -> str:
        return f"""Analyze this procurement insight and provide detailed analysis:

Type: {insight['type']}
Title: {insight['title']}
Description: {insight['description']}
Severity: {insight['severity']}
Potential Savings: ${insight.get('potential_savings', 0):,.2f}
Confidence: {insight.get('confidence', 0) * 100:.0f}%

Additional Details:
{json.dumps(insight.get('details', {}), indent=2)}

Provide root cause analysis, industry benchmarks, and actionable remediation steps."""

    def _build_deep_analysis_prompt(self, insight_data: dict, context: dict) -> str:
        return f"""Perform a comprehensive deep analysis of this procurement insight.

INSIGHT DETAILS:
- ID: {insight_data.get('id', 'N/A')}
- Type: {insight_data.get('type', 'N/A')}
- Title: {insight_data.get('title', 'N/A')}
- Description: {insight_data.get('description', 'N/A')}
- Severity: {insight_data.get('severity', 'N/A')}
- Confidence: {insight_data.get('confidence', 0) * 100:.0f}%
- Potential Savings: ${insight_data.get('potential_savings', 0):,.2f}

ADDITIONAL DETAILS:
{json.dumps(insight_data.get('details', {}), indent=2)}

RECOMMENDED ACTIONS (from initial analysis):
{json.dumps(insight_data.get('recommended_actions', []), indent=2)}

ORGANIZATION CONTEXT:
{json.dumps(context, indent=2)}

Provide a thorough analysis including:
1. Root cause analysis - identify the primary cause and contributing factors
2. Implementation roadmap - phased approach with specific tasks
3. Financial impact - detailed savings breakdown and ROI calculation
4. Risk factors - potential risks and mitigation strategies
5. Success metrics - KPIs to track implementation success
6. Stakeholder mapping - who needs to be involved
7. Industry context - benchmarks and best practices
8. Clear next steps - immediate actions to take"""


class OpenAIProvider(AIProvider):
    """OpenAI GPT API provider implementation."""

    name = "openai"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        if not self._client and self.api_key:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("openai package not installed")
        return self._client

    def is_available(self) -> bool:
        return bool(self.api_key and self.client)

    def health_check(self) -> dict:
        if not self.is_available():
            return {"healthy": False, "latency_ms": 0, "error": "Not configured"}

        import time
        start = time.time()
        try:
            self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5
            )
            latency = int((time.time() - start) * 1000)
            return {"healthy": True, "latency_ms": latency, "error": None}
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return {"healthy": False, "latency_ms": latency, "error": str(e)}

    def _convert_to_openai_tool(self, tool_schema: dict) -> dict:
        """Convert Anthropic tool schema to OpenAI format."""
        return {
            "type": "function",
            "function": {
                "name": tool_schema["name"],
                "description": tool_schema["description"],
                "parameters": tool_schema["input_schema"]
            }
        }

    def enhance_insights(
        self,
        insights: list,
        context: dict,
        tool_schema: dict
    ) -> Optional[dict]:
        if not self.is_available():
            return None

        try:
            openai_tool = self._convert_to_openai_tool(tool_schema)

            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a procurement analytics expert. Analyze the insights and provide structured, actionable recommendations."
                    },
                    {
                        "role": "user",
                        "content": self._build_enhancement_prompt(insights, context)
                    }
                ],
                tools=[openai_tool],
                tool_choice={"type": "function", "function": {"name": tool_schema["name"]}},
                max_tokens=2048
            )

            if response.choices and response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                result = json.loads(tool_call.function.arguments)
                result['provider'] = 'openai'
                result['generated_at'] = datetime.now().isoformat()
                return result

            logger.warning("OpenAI did not return function call response")
            return None

        except Exception as e:
            logger.error(f"OpenAI enhancement failed: {e}")
            raise

    def analyze_single_insight(
        self,
        insight: dict,
        tool_schema: dict
    ) -> Optional[dict]:
        if not self.is_available():
            return None

        try:
            openai_tool = self._convert_to_openai_tool(tool_schema)

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a procurement analytics expert. Provide concise, actionable analysis."
                    },
                    {
                        "role": "user",
                        "content": self._build_single_insight_prompt(insight)
                    }
                ],
                tools=[openai_tool],
                tool_choice={"type": "function", "function": {"name": tool_schema["name"]}},
                max_tokens=500
            )

            if response.choices and response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                result = json.loads(tool_call.function.arguments)
                result['provider'] = 'openai'
                result['model'] = 'gpt-4o-mini'
                result['generated_at'] = datetime.now().isoformat()
                return result

            return None

        except Exception as e:
            logger.error(f"OpenAI single insight analysis failed: {e}")
            raise

    def deep_analysis(
        self,
        insight_data: dict,
        context: dict,
        tool_schema: dict
    ) -> Optional[dict]:
        if not self.is_available():
            return None

        try:
            openai_tool = self._convert_to_openai_tool(tool_schema)

            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior procurement consultant providing comprehensive analysis. Be thorough, specific, and actionable."
                    },
                    {
                        "role": "user",
                        "content": self._build_deep_analysis_prompt(insight_data, context)
                    }
                ],
                tools=[openai_tool],
                tool_choice={"type": "function", "function": {"name": tool_schema["name"]}},
                max_tokens=4096
            )

            if response.choices and response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                result = json.loads(tool_call.function.arguments)
                result['insight_id'] = insight_data.get('id')
                result['provider'] = 'openai'
                result['model'] = 'gpt-4-turbo'
                result['generated_at'] = datetime.now().isoformat()
                return result

            return None

        except Exception as e:
            logger.error(f"OpenAI deep analysis failed: {e}")
            raise

    def _build_enhancement_prompt(self, insights: list, context: dict) -> str:
        return f"""Analyze these procurement insights and provide structured recommendations.

Organization: {context['organization']['name']}

Spending Summary:
- Total YTD Spend: ${context['spending']['total_ytd']:,.2f}
- Supplier Count: {context['spending']['supplier_count']}
- Category Count: {context['spending']['category_count']}

Current Insights ({len(insights)} total):
{json.dumps(context['insights'], indent=2)}

Provide actionable recommendations prioritized by impact and effort."""

    def _build_single_insight_prompt(self, insight: dict) -> str:
        return f"""Analyze this procurement insight:

Type: {insight['type']}
Title: {insight['title']}
Description: {insight['description']}
Severity: {insight['severity']}
Potential Savings: ${insight.get('potential_savings', 0):,.2f}

Provide root cause analysis and actionable remediation steps."""

    def _build_deep_analysis_prompt(self, insight_data: dict, context: dict) -> str:
        return f"""Perform a comprehensive deep analysis of this procurement insight.

INSIGHT DETAILS:
- Type: {insight_data.get('type', 'N/A')}
- Title: {insight_data.get('title', 'N/A')}
- Description: {insight_data.get('description', 'N/A')}
- Severity: {insight_data.get('severity', 'N/A')}
- Potential Savings: ${insight_data.get('potential_savings', 0):,.2f}

CONTEXT:
{json.dumps(context, indent=2)}

Provide thorough analysis with root cause, implementation roadmap, financial impact, risks, and next steps."""


class AIProviderManager:
    """
    Manages AI providers with automatic failover.

    Attempts the primary provider first, then falls back through
    the fallback chain on failure.
    """

    PROVIDER_CLASSES = {
        'anthropic': AnthropicProvider,
        'openai': OpenAIProvider,
    }

    def __init__(
        self,
        primary_provider: str,
        api_keys: Dict[str, str],
        fallback_order: List[str] = None,
        enable_fallback: bool = True
    ):
        """
        Initialize the provider manager.

        Args:
            primary_provider: Primary provider name ('anthropic' or 'openai')
            api_keys: Dict mapping provider names to API keys
            fallback_order: Order of providers to try (defaults to ['anthropic', 'openai'])
            enable_fallback: Whether to enable automatic failover
        """
        self.primary_provider = primary_provider
        self.api_keys = api_keys or {}
        self.fallback_order = fallback_order or ['anthropic', 'openai']
        self.enable_fallback = enable_fallback

        self._providers: Dict[str, AIProvider] = {}
        self._provider_errors: Dict[str, str] = {}
        self._last_successful_provider: Optional[str] = None

        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize all available providers."""
        for name, api_key in self.api_keys.items():
            if api_key and name in self.PROVIDER_CLASSES:
                try:
                    self._providers[name] = self.PROVIDER_CLASSES[name](api_key)
                    logger.info(f"Initialized {name} provider")
                except Exception as e:
                    logger.warning(f"Failed to initialize {name} provider: {e}")
                    self._provider_errors[name] = str(e)

    def _get_providers_to_try(self) -> List[str]:
        """Get ordered list of providers to attempt."""
        providers = [self.primary_provider]
        if self.enable_fallback:
            providers.extend(p for p in self.fallback_order if p != self.primary_provider)
        return providers

    def get_provider(self, name: str) -> Optional[AIProvider]:
        """Get a specific provider instance."""
        return self._providers.get(name)

    def get_available_providers(self) -> List[str]:
        """Get list of available (configured) providers."""
        return [name for name, provider in self._providers.items() if provider.is_available()]

    def health_check_all(self) -> Dict[str, dict]:
        """Perform health check on all providers."""
        results = {}
        for name, provider in self._providers.items():
            results[name] = provider.health_check()
        return results

    def enhance_insights(
        self,
        insights: list,
        context: dict,
        tool_schema: dict
    ) -> Optional[dict]:
        """
        Enhance insights with automatic failover.

        Args:
            insights: List of insight dictionaries
            context: Comprehensive context for AI analysis
            tool_schema: Tool/function schema for structured output

        Returns:
            Enhancement dict with 'provider' field indicating which provider succeeded,
            or None if all providers fail
        """
        providers_to_try = self._get_providers_to_try()
        last_error = None

        for provider_name in providers_to_try:
            provider = self._providers.get(provider_name)
            if not provider or not provider.is_available():
                logger.debug(f"Skipping unavailable provider: {provider_name}")
                continue

            try:
                logger.info(f"Attempting insight enhancement with {provider_name}")
                result = provider.enhance_insights(insights, context, tool_schema)
                if result:
                    self._last_successful_provider = provider_name
                    logger.info(f"Enhancement succeeded with {provider_name}")
                    return result
            except Exception as e:
                last_error = e
                self._provider_errors[provider_name] = str(e)
                logger.warning(f"Provider {provider_name} failed: {e}")
                if not self.enable_fallback:
                    break
                continue

        logger.error(f"All providers failed for enhancement. Last error: {last_error}")
        return None

    def analyze_single_insight(
        self,
        insight: dict,
        tool_schema: dict
    ) -> Optional[dict]:
        """Analyze single insight with automatic failover."""
        providers_to_try = self._get_providers_to_try()
        last_error = None

        for provider_name in providers_to_try:
            provider = self._providers.get(provider_name)
            if not provider or not provider.is_available():
                continue

            try:
                logger.debug(f"Attempting single insight analysis with {provider_name}")
                result = provider.analyze_single_insight(insight, tool_schema)
                if result:
                    self._last_successful_provider = provider_name
                    return result
            except Exception as e:
                last_error = e
                self._provider_errors[provider_name] = str(e)
                logger.warning(f"Provider {provider_name} failed for single insight: {e}")
                if not self.enable_fallback:
                    break
                continue

        logger.error(f"All providers failed for single insight. Last error: {last_error}")
        return None

    def deep_analysis(
        self,
        insight_data: dict,
        context: dict,
        tool_schema: dict
    ) -> Optional[dict]:
        """Perform deep analysis with automatic failover."""
        providers_to_try = self._get_providers_to_try()
        last_error = None

        for provider_name in providers_to_try:
            provider = self._providers.get(provider_name)
            if not provider or not provider.is_available():
                continue

            try:
                logger.info(f"Attempting deep analysis with {provider_name}")
                result = provider.deep_analysis(insight_data, context, tool_schema)
                if result:
                    self._last_successful_provider = provider_name
                    logger.info(f"Deep analysis succeeded with {provider_name}")
                    return result
            except Exception as e:
                last_error = e
                self._provider_errors[provider_name] = str(e)
                logger.warning(f"Provider {provider_name} failed for deep analysis: {e}")
                if not self.enable_fallback:
                    break
                continue

        logger.error(f"All providers failed for deep analysis. Last error: {last_error}")
        return None

    def get_status(self) -> dict:
        """
        Get comprehensive status of all providers.

        Returns:
            Dict with provider status information for monitoring
        """
        return {
            "primary_provider": self.primary_provider,
            "fallback_enabled": self.enable_fallback,
            "last_successful_provider": self._last_successful_provider,
            "available_providers": self.get_available_providers(),
            "provider_errors": self._provider_errors.copy(),
            "providers": {
                name: {
                    "available": provider.is_available(),
                    "last_error": self._provider_errors.get(name)
                }
                for name, provider in self._providers.items()
            }
        }

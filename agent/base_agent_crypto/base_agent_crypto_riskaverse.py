"""
BaseAgentCryptoRiskAverse — Modification Agent for HW3 Reproducibility Study

Change from baseline (BaseAgentCrypto):
  - Uses prompts/agent_prompt_crypto_riskaverse.py instead of agent_prompt_crypto.py
  - The modified prompt adds explicit risk management constraints:
      (1) 35% max position per asset
      (2) Mandatory hold-vs-trade assessment
      (3) Minimum 3-asset diversification
      (4) 10% mandatory cash reserve
  - All other parameters (MCP config, LLM, tools) are IDENTICAL to baseline

Purpose: Evaluate whether adding risk management rules to the system prompt
         improves risk-adjusted returns (Sortino Ratio, MDD) without significantly
         reducing cumulative return.
"""

from agent.base_agent_crypto.base_agent_crypto import BaseAgentCrypto
from prompts.agent_prompt_crypto_riskaverse import (
    STOP_SIGNAL, get_agent_system_prompt_crypto_riskaverse)


class BaseAgentCryptoRiskAverse(BaseAgentCrypto):
    """
    Risk-constrained variant of the base crypto trading agent.
    Overrides only the system prompt generation; all other logic is inherited.
    """

    async def run_trading_session(self, today_date: str) -> None:
        """
        Run single day trading session with risk-averse system prompt.
        Overrides parent to inject the modified prompt.
        """
        from langchain.agents import create_agent

        from tools.general_tools import write_config_value
        from tools.price_tools import add_no_trade_record

        print(f"📈 [RiskAverse] Starting crypto trading session: {today_date}")

        log_file = self._setup_logging(today_date)
        write_config_value("LOG_FILE", log_file)

        # KEY CHANGE: use modified risk-averse prompt
        self.agent = create_agent(
            self.model,
            tools=self.tools,
            system_prompt=get_agent_system_prompt_crypto_riskaverse(
                today_date, self.signature, self.market, self.crypto_symbols
            ),
        )

        user_query = [{"role": "user", "content": f"Please analyze and update today's ({today_date}) positions."}]
        message = user_query.copy()
        self._log_message(log_file, user_query)

        current_step = 0
        while current_step < self.max_steps:
            current_step += 1
            print(f"🔄 [RiskAverse] Step {current_step}/{self.max_steps}")

            try:
                from tools.general_tools import extract_conversation, extract_tool_messages

                response = await self._ainvoke_with_retry(message)
                agent_response = extract_conversation(response, "final")

                if STOP_SIGNAL in agent_response:
                    print("✅ [RiskAverse] Received stop signal, trading session ended")
                    print(agent_response)
                    self._log_message(log_file, [{"role": "assistant", "content": agent_response}])
                    break

                tool_msgs = extract_tool_messages(response)
                tool_response = "\n".join([msg.content for msg in tool_msgs])

                new_messages = [
                    {"role": "assistant", "content": agent_response},
                    {"role": "user", "content": f"Tool results: {tool_response}"},
                ]
                message.extend(new_messages)
                self._log_message(log_file, new_messages[0])
                self._log_message(log_file, new_messages[1])

            except Exception as e:
                print(f"❌ [RiskAverse] Trading session error: {str(e)}")
                raise

        await self._handle_trading_result(today_date)

    def __str__(self) -> str:
        return (
            f"BaseAgentCryptoRiskAverse(signature='{self.signature}', "
            f"basemodel='{self.basemodel}', cryptos={len(self.crypto_symbols)})"
        )

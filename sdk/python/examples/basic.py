from prompt_engine import PromptOptimizationEngine


def main() -> None:
    engine = PromptOptimizationEngine()
    result = engine.optimize_prompt(
        "Extract the pricing, contract length, and renewal owner from this commercial email.",
        context={
            "output_schema": {
                "type": "object",
                "properties": {
                    "pricing": {"type": "string"},
                    "contract_length": {"type": "string"},
                    "renewal_owner": {"type": "string"},
                },
                "required": ["pricing", "contract_length", "renewal_owner"],
            }
        },
    )
    print(result.final_prompt)


if __name__ == "__main__":
    main()


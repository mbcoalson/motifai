import logging

class OpenAICostCalculator:
    # Define pricing per 1,000 tokens (in USD)
    PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006}
    }

    def __init__(self, log_file="openai_costs.log"):
        self.total_cost = 0.0
        logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s")

    def calculate_cost(self, model, input_tokens, output_tokens):
        """Calculate the cost for a single API call."""
        if model not in self.PRICING:
            raise ValueError(f"Model {model} is not in the pricing list.")
        
        # Calculate cost
        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        total = input_cost + output_cost

        # Add to total cost
        self.total_cost += total

        # Log the cost
        logging.info(f"Model: {model}, Input Tokens: {input_tokens}, Output Tokens: {output_tokens}, Cost: ${total:.4f}, Total Cost: ${self.total_cost:.4f}")

        return total

    def get_total_cost(self):
        """Return the total accumulated cost."""
        return self.total_cost

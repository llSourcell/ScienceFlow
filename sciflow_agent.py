import os
from openai import OpenAI

class ScienceFlowAgent:
    def __init__(self):
        self.client = OpenAI(api_key="ENTER KEY HERE")

    def generate_pipeline(self, prompt: str) -> str:
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are an AI research assistant specializing in number theory and formal verification.
You are proficient in the Lean theorem prover and can generate mathematically rigorous proofs.

For unproven conjectures or open problems:
1. Clearly state that the problem is currently unproven
2. Provide a formal statement in Lean of what we're trying to prove
3. Include any known partial results or lemmas that have been proven
4. Provide a proof sketch or outline of potential proof strategies"""},
                    {"role": "user", "content": f"""Given the prompt: '{prompt}', generate a structured scientific pipeline including:
1. Literature review summary related to the number theory problem.
2. A number-theoretic hypothesis or conjecture clearly stated in mathematical notation.
3. Formal statement in Lean:
   - For proven results: provide the complete theorem and proof
   - For unproven conjectures: provide the theorem statement and any proven supporting lemmas
4. Proof content (choose appropriate option):
   A) For proven results:
      - Required imports and dependencies
      - Complete proof in Lean
   B) For unproven conjectures:
      - Known partial results in Lean
      - Proof sketch of potential approaches
      - Any helper lemmas that have been proven
5. Experimental test plan to verify the hypothesis empirically.
6. Expected results and current evidence.
7. A draft short paper summary.

Format the Lean code sections with ```lean at the start and ``` at the end.
Always include at least a formal statement in Lean, even for unproven conjectures."""}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating pipeline: {str(e)}")
            return (
                "1. Literature Review: [Dummy content]\n\n"
                "2. Hypothesis: For all primes p > 3, p ≡ 1 or 5 (mod 6).\n\n"
                "3. Lean Statement:\n```lean\ntheorem prime_mod_six (p : ℕ) (h_prime : prime p) (h_gt_three : p > 3) :\n  p % 6 = 1 ∨ p % 6 = 5\n```\n\n"
                "4. Lean Proof:\n```lean\nimport data.nat.prime\nimport data.nat.modeq\n\ntheorem prime_mod_six (p : ℕ) (h_prime : prime p) (h_gt_three : p > 3) :\n  p % 6 = 1 ∨ p % 6 = 5 := sorry\n```\n\n"
                "5. Experimentation Plan: Check primes up to 10000.\n\n"
                "6. Expected Results: No counterexamples.\n\n"
                "7. Draft Paper: [Dummy summary]"
            )
import os
from openai import OpenAI

class ReviewerAgents:
    def __init__(self):
        self.client = OpenAI(api_key="ENTER KEY HERE")

    def get_peer_review(self, pipeline_result: str, verification_report: str):
        try:
            reviewers = [
                "You are a conservative mathematician who values formal proof and rigor. Provide a critical review.",
                "You are an experimental number theorist who values empirical evidence. Provide feedback.",
                "You are a journal editor focusing on clarity and novelty. Provide editorial feedback."
            ]

            aggregated_reviews = []
            for reviewer_role in reviewers:
                completion = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": reviewer_role},
                        {"role": "user", "content": f"""Please review the following:

Pipeline Result:
{pipeline_result}

Verification Report:
{verification_report}

Please provide a constructive peer review."""}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
                review = completion.choices[0].message.content.strip()
                aggregated_reviews.append(review)

            return "\n\n".join(aggregated_reviews)
            
        except Exception as e:
            print(f"Error generating peer review: {str(e)}")
            return (
                "Reviewer 1: The reasoning seems sound, but more rigorous proof is needed.\n"
                "Reviewer 2: Interesting hypothesis, but please include references.\n"
                "Reviewer 3: Good start, consider formalizing the conjecture more explicitly."
            )
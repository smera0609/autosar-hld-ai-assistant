import re
import ollama


class OllamaProvider:
    """
    Local LLM provider for the AUTOSAR HLD
    analysis assistant.
    """

    def __init__(
        self,
        model: str = "qwen3:4b-instruct",
    ):
        self.model = model

    def generate(
        self,
        prompt: str,
    ) -> str:

        if not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty."
            )

        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                think=False,
                options={
                "temperature": 0.0,
                "num_predict": 200,
                },

                    # Give Qwen enough room to finish
                    # its reasoning and produce the
                    # final answer.
                 
            )

        except Exception as exc:
            raise RuntimeError(
                f"Ollama generation failed: {exc}"
            ) from exc

        answer = (
            response.message.content or ""
        ).strip()

        if not answer:
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        # -----------------------------------------
        # REMOVE QWEN THINKING
        # -----------------------------------------

        # Qwen may return:
        #
        # reasoning...
        # </think>
        # VehicleSpeedController
        #
        # Keep only the part after </think>.

        if "</think>" in answer:
            answer = answer.rsplit(
                "</think>",
                1,
            )[-1].strip()

        # Handle normal:
        # <think> ... </think>
        answer = re.sub(
            r"<think>.*?</think>",
            "",
            answer,
            flags=re.DOTALL,
        ).strip()

        # -----------------------------------------
        # REMOVE OPTIONAL LABELS
        # -----------------------------------------

        labels = [
            "FINAL ANSWER:",
            "Final Answer:",
            "Final answer:",
            "Answer:",
        ]

        for label in labels:
            if answer.startswith(label):
                answer = answer[
                    len(label):
                ].strip()

        if not answer:
            raise RuntimeError(
                "No final answer remained after "
                "cleaning the model response."
            )

        return answer
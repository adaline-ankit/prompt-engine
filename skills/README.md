# External Skill Plugins

Prompt Engine loads plugin modules from the directories listed under `skills.plugin_paths` in [config/config.yaml](../config/config.yaml).

Each plugin module should expose `register()` or `register_skills()` and return one `Skill` instance or a list of `Skill` instances.

Example:

```python
from prompt_engine.models import PromptState
from prompt_engine.skills.base import Skill


class ExamplePolicySkill(Skill):
    name = "example_policy"
    category = "safety"
    priority = 40

    def should_trigger(self, state: PromptState, context: dict) -> bool:
        return state.intent == "reasoning"

    def transform(self, state: PromptState, context: dict) -> PromptState:
        state.constraints.append("Explicitly separate known facts from assumptions.")
        self.record_transformation(
            state,
            description="Adds a policy constraint for reasoning tasks.",
            before="No fact/assumption split.",
            after="Requires facts and assumptions to be separated.",
        )
        return state


def register():
    return [ExamplePolicySkill()]
```

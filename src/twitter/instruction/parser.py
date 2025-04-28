from twitter.instruction.timeline.clear_cache import parse as ParseClearCache
from twitter.instruction.timeline.pin_entry import parse as ParsePinEntry
from twitter.instruction.timeline.add_entries import parse as ParseAddEntries

from twitter.tweet import Tweet

_handler = {
    'TimelineClearCache': ParseClearCache,
    'TimelinePinEntry': ParsePinEntry,
    'TimelineAddEntries': ParseAddEntries,
}


class InstructionParser:
    data = {}

    def __init__(self, insts: dict):
        self.data = insts

    def parse(self) -> list[Tweet]:
        result = []
        for instruction in self.data:
            item_type = instruction['type']
            if item_type not in _handler:
                print(f'unknown instruction type: {item_type}')
                continue
            _handler[item_type](result, instruction)
        return result

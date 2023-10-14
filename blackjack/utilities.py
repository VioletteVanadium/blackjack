import itertools as it
from collections import deque
from typing import Any

from arcade import Text, color, easing


def centered_text(
    contents,
    start_x,
    start_y,
    color=color.WHITE,
    align="center",
    anchor_x="center",
    anchor_y="center",
    width=300,
    **kwargs
) -> Text:
    return Text(
        str(contents),
        start_x=start_x,
        start_y=start_y,
        color=color,
        align="center",
        anchor_x="center",
        anchor_y="center",
        **kwargs,
    )


class ParallelEasing:
    def __init__(self, start_time: float = 0.0):
        self.start_time = start_time
        self.elapsed_time = 0.0
        self.easing_data: deque[
            tuple[float, Any, str, easing.EasingData]
        ] = deque([])
        self.function_data: deque[tuple[float, Any, str, tuple, dict]] = deque(
            []
        )

    @property
    def finished(self):
        return len(self.easing_data) == 0 and len(self.function_data) == 0

    @property
    def objects(self):
        return [
            item[1] for item in it.chain(self.easing_data, self.function_data)
        ]

    def reset(self):
        self.elapsed_time = 0.0
        self.easing_data = []
        self.function_data = []

    def add_easing_data(
        self,
        obj: Any,
        attribute: str,
        easing_data: easing.EasingData,
        delay: float = 0.0,
    ):
        self.easing_data.append(
            (self.start_time + delay, obj, attribute, easing_data)
        )

    def add_function_data(
        self,
        obj: Any,
        function_name: str,
        args: tuple,
        kwargs: dict,
        delay: float = 0.0,
    ):
        self.function_data.append(
            (self.start_time + delay, obj, function_name, args, kwargs)
        )

    def _update_easing_data(self, delta_time: float):
        finished = []
        for start, obj, attr, data in self.easing_data:
            if start > self.elapsed_time:
                continue
            done, value = easing.ease_update(data, delta_time)
            setattr(obj, attr, value)
            if done:
                # occasionally, we don't line up just right, I assume due to
                # rounding errors
                setattr(obj, attr, data.end_value)
                finished.append((start, obj, attr, data))
        for item in finished:
            self.easing_data.remove(item)

    def _update_function_data(self, delta_time: float):
        finished = []
        for start, obj, func, args, kwargs in self.function_data:
            if start > self.elapsed_time:
                continue
            if func is not None:
                getattr(obj, func)(*args, **kwargs)
            else:
                obj(*args, **kwargs)
            finished.append((start, obj, func, args, kwargs))
        for item in finished:
            self.function_data.remove(item)

    def on_update(self, delta_time: float):
        self.elapsed_time += delta_time
        self._update_easing_data(delta_time)
        self._update_function_data(delta_time)


class SequenceEasing(deque[ParallelEasing]):
    @property
    def finished(self) -> bool:
        return len(self) == 0

    @property
    def objects(self) -> list[Any]:
        return list(it.chain.from_iterable(x.objects for x in self))

    def series(self) -> ParallelEasing:
        rv = ParallelEasing()
        self.append(rv)
        return rv

    def parallel(self) -> ParallelEasing:
        return self[-1]

    def on_update(self, delta_time: float) -> bool:
        if self.finished:
            return True
        finished = []
        for i, parallel in enumerate(self):
            parallel.on_update(delta_time)
            if not parallel.finished:
                break
            finished.append(parallel)
        for item in finished:
            self.remove(item)
        if self.finished:
            return True
        return False

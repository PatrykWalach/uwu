const id = (id) => {
  return id;
};
const unit = undefined;
const reduce = (arr) => (reducer) => (acc) => {
  return arr.reduce((acc, v) => reducer(acc)(v), acc);
};
const console_log = (value) => {
  return console.log(value);
};
const traverse = (arr) => (fn) => {
  const reducer = (acc) => (value) => {
    return (() => {
      const $ = id(acc);
      if ($ === "None") {
        return "None";
      }
      if (typeof $ !== "string" && $.TAG === "Some") {
        const acc_value = $._0;
        return (() => {
          const $ = fn(value);
          if (typeof $ !== "string" && $.TAG === "Some") {
            const next_value = $._0;
            return { TAG: "Some", _0: acc_value.concat([next_value]) };
          }
          if ($ === "None") {
            return "None";
          }
          throw new Error("Non-exhaustive pattern match");
        })();
      }
      throw new Error("Non-exhaustive pattern match");
    })();
  };
  return reduce(arr)(reducer)({ TAG: "Some", _0: [] });
};
const min = (a) => (b) => {
  return (() => {
    if (a < b) {
      return a;
    }
    return b;
  })();
};
const max = (a) => (b) => {
  return (() => {
    if (a > b) {
      return a;
    }
    return b;
  })();
};
const len = (arr) => {
  return arr.length;
};
const head = (arr) => {
  return (() => {
    if (len(arr) < 1.0) {
      return "Empty";
    }
    const [_head, ..._rest] = arr;
    const list_head = _head;
    const rest = _rest;
    return { TAG: "Head", _0: list_head, _1: rest };
  })();
};
const bubble_sort = (cmp) => (arr) => {
  const swap_till = (acc) => (value) => {
    const swap_till2 = swap_till;
    return (() => {
      const $ = head(acc);
      if ($ === "Empty") {
        return [value];
      }
      if (typeof $ !== "string" && $.TAG === "Head") {
        const arr_head = $._0;
        const rest = $._1;
        return (() => {
          if (cmp(value)(arr_head) < 0.0) {
            return [value].concat(swap_till2(rest)(arr_head));
          }
          return [arr_head].concat(swap_till2(rest)(value));
        })();
      }
      throw new Error("Non-exhaustive pattern match");
    })();
  };
  return reduce(arr)(swap_till)([]);
};
const merge = (a) => (b) => {
  const merge2 = merge;
  return (() => {
    const $ = { TAG: "Tuple", _0: head(a), _1: head(b) };
    if (typeof $ !== "string" && $.TAG === "Tuple") {
      if ($._0 === "Empty") {
        const _ = $._1;
        return b;
      }
      if ($._1 === "Empty") {
        const _ = $._0;
        return a;
      }
      if (typeof $._0 !== "string" && $._0.TAG === "Head") {
        if (typeof $._1 !== "string" && $._1.TAG === "Head") {
          const head_b = $._1._0;
          const rest_b = $._1._1;
          const head_a = $._0._0;
          const rest_a = $._0._1;
          return (() => {
            if (head_a < head_b) {
              return [head_a].concat(merge2(rest_a)(b));
            }
            return [head_b].concat(merge2(a)(rest_b));
          })();
        }
        throw new Error("Non-exhaustive pattern match");
      }
      throw new Error("Non-exhaustive pattern match");
    }
    throw new Error("Non-exhaustive pattern match");
  })();
};
const take = (arr) => (n) => {
  return arr.slice(0, n);
};
const drop = (arr) => (n) => {
  return arr.slice(n);
};
const merge_sort = (arr) => {
  const merge_sort2 = merge_sort;
  return (() => {
    if (len(arr) < 2.0) {
      return arr;
    }
    const right = merge_sort2(take(arr)(Math.floor(len(arr) / 2.0)));
    const left = merge_sort2(drop(arr)(Math.floor(len(arr) / 2.0)));
    return merge(right)(left);
  })();
};
const number__cmp = (a) => (b) => {
  return a - b;
};
const number__bubble_sort = bubble_sort(number__cmp);
console_log(number__bubble_sort([17.0, 9.0, 21.0, 3.0, 0.0]));
console_log(merge_sort([17.0, 9.0, 21.0, 3.0, 0.0]));
(() => {
  const $ = { TAG: "Some", _0: 1.0 };
  if (typeof $ !== "string" && $.TAG === "Some") {
    const x = $._0;
    return unit;
  }
  if ($ === "None") {
    return unit;
  }
  throw new Error("Non-exhaustive pattern match");
})();
(() => {
  const $ = { TAG: "Tuple", _0: 1.0, _1: "12" };
  if (typeof $ !== "string" && $.TAG === "Tuple") {
    const _ = $._1;
    return unit;
  }
  throw new Error("Non-exhaustive pattern match");
})();

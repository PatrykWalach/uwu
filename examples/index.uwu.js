function id(id) {
  return id;
}
const unit = undefined;
function reduce(arr) {
  return (reducer) => (acc) => arr.reduce((acc, v) => reducer(acc)(v), acc);
}
function console_log(value) {
  return console.log(value);
}
function traverse(arr) {
  return (fn) => {
    function reducer(acc) {
      return (value) =>
        (() => {
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
    }
    return reduce(arr)(reducer)({ TAG: "Some", _0: [] });
  };
}
function min(a) {
  return (b) => {
    if (a < b) {
      return a;
    }
    return b;
  };
}
function max(a) {
  return (b) => {
    if (a > b) {
      return a;
    }
    return b;
  };
}
function len(arr) {
  return arr.length;
}
function head(arr) {
  if (len(arr) < 1.0) {
    return "Empty";
  }
  const [_head, ..._rest] = arr;
  const list_head = _head;
  const rest = _rest;
  return { TAG: "Head", _0: list_head, _1: rest };
}
function bubble_sort(cmp) {
  return (arr) => {
    function swap_till(acc) {
      return (value) => {
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
    }
    return reduce(arr)(swap_till)([]);
  };
}
function merge(a) {
  return (b) => {
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
}
function take(arr) {
  return (n) => arr.slice(0, n);
}
function drop(arr) {
  return (n) => arr.slice(n);
}
function merge_sort(arr) {
  const merge_sort2 = merge_sort;
  return (() => {
    if (len(arr) < 2.0) {
      return arr;
    }
    const right = merge_sort2(take(arr)(Math.floor(len(arr) / 2.0)));
    const left = merge_sort2(drop(arr)(Math.floor(len(arr) / 2.0)));
    return merge(right)(left);
  })();
}
function number__cmp(a) {
  return (b) => a - b;
}
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
function chain_do(option) {
  return (fn) =>
    (() => {
      const $ = option;
      if (typeof $ !== "string" && $.TAG === "Some") {
        const value = $._0;
        return (() => {
          const $ = fn(value);
          if (typeof $ !== "string" && $.TAG === "Some") {
            const result = $._0;
            return { TAG: "Some", _0: { TAG: "Tuple", _0: value, _1: result } };
          }
          if ($ === "None") {
            return "None";
          }
          throw new Error("Non-exhaustive pattern match");
        })();
      }
      if ($ === "None") {
        return "None";
      }
      throw new Error("Non-exhaustive pattern match");
    })();
}
function div(a) {
  return (b) => {
    if (!Object.is(b, 0.0)) {
      return { TAG: "Some", _0: Math.floor(a / b) };
    }
    return "None";
  };
}
function chain_return(option) {
  return (fn) =>
    (() => {
      const $ = option;
      if (typeof $ !== "string" && $.TAG === "Some") {
        const value = $._0;
        return fn(value);
      }
      if ($ === "None") {
        return "None";
      }
      throw new Error("Non-exhaustive pattern match");
    })();
}
const a = { TAG: "Some", _0: 2.0 };
const b = chain_do(a)(div(6.0));
const c = chain_do(b)(function chain_1(value) {
  return (() => {
    const $ = value;
    if (typeof $ !== "string" && $.TAG === "Tuple") {
      const a = $._0;
      const b = $._1;
      return { TAG: "Some", _0: a * b };
    }
    throw new Error("Non-exhaustive pattern match");
  })();
});
const d = chain_return(c)(function chain_2(value) {
  return (() => {
    const $ = value;
    if (typeof $ !== "string" && $.TAG === "Tuple") {
      if (typeof $._0 !== "string" && $._0.TAG === "Tuple") {
        const a = $._0._0;
        const b = $._0._1;
        const c = $._1;
        return { TAG: "Some", _0: a + b + c };
      }
      throw new Error("Non-exhaustive pattern match");
    }
    throw new Error("Non-exhaustive pattern match");
  })();
});
console_log(d);

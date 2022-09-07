const id = (x) => {
  return x;
};
const unit = undefined;
const /* + */ op1 = (a) => (b) => {
    return a + b;
  };
const /* / */ op4 = (a) => (b) => {
    return Math.floor(a / b);
  };
const /* * */ op2 = (a) => (b) => {
    return a * b;
  };
const /* - */ op5 = (a) => (b) => {
    return a - b;
  };
const /* < */ op6 = (a) => (b) => {
    return a < b;
  };
const /* > */ op7 = (a) => (b) => {
    return a > b;
  };
const /* != */ op8 = (a) => (b) => {
    return !Object.is(a, b);
  };
const /* ++ */ op9 = (a) => (b) => {
    return a.concat(b);
  };
const reduce = (arr) => (reducer) => (acc) => {
  return arr.reduce((acc, v) => reducer(acc)(v), acc);
};
const console_log = (value) => {
  return console.log(value);
};
const len = (arr) => {
  return arr.length;
};
const head = (arr) => {
  return (() => {
    if (op6(len(arr))(/* < */ 1.0)) {
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
          if (op6(cmp(value)(arr_head))(/* < */ 0.0)) {
            return op9([value])(/* ++ */ swap_till2(rest)(arr_head));
          }
          return op9([arr_head])(/* ++ */ swap_till2(rest)(value));
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
            if (op6(head_a)(/* < */ head_b)) {
              return op9([head_a])(/* ++ */ merge2(rest_a)(b));
            }
            return op9([head_b])(/* ++ */ merge2(a)(rest_b));
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
    if (op6(len(arr))(/* < */ 2.0)) {
      return arr;
    }
    const right = merge_sort2(take(arr)(op4(len(arr))(/* / */ 2.0)));
    const left = merge_sort2(drop(arr)(op4(len(arr))(/* / */ 2.0)));
    return merge(right)(left);
  })();
};
const number__cmp = (a) => (b) => {
  return op5(a)(/* - */ b);
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
const chain_do = (option) => (fn) => {
  return (() => {
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
};
const div = (a) => (b) => {
  return (() => {
    if (op8(b)(/* != */ 0.0)) {
      return { TAG: "Some", _0: op4(a)(/* / */ b) };
    }
    return "None";
  })();
};
const chain_return = (option) => (fn) => {
  return (() => {
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
};
const a = { TAG: "Some", _0: 2.0 };
const b = chain_do(a)(div(6.0));
const chain_1 = (value) => {
  return (() => {
    const $ = value;
    if (typeof $ !== "string" && $.TAG === "Tuple") {
      const a = $._0;
      const b = $._1;
      return { TAG: "Some", _0: op2(a)(/* * */ b) };
    }
    throw new Error("Non-exhaustive pattern match");
  })();
};
const c = chain_do(b)(chain_1);
const chain_2 = (value) => {
  return (() => {
    const $ = value;
    if (typeof $ !== "string" && $.TAG === "Tuple") {
      if (typeof $._0 !== "string" && $._0.TAG === "Tuple") {
        const a = $._0._0;
        const b = $._0._1;
        const c = $._1;
        return { TAG: "Some", _0: op1(op1(a)(/* + */ b))(/* + */ c) };
      }
      throw new Error("Non-exhaustive pattern match");
    }
    throw new Error("Non-exhaustive pattern match");
  })();
};
const d = chain_return(c)(chain_2);
console_log(d);

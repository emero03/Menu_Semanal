/* Backend simulado para la vista previa: replica en JS el gestor de Python
 * (custom_components/menu_semanal: nutrition.py, planner.py, pantry.py y manager.py),
 * con una Despensa y una Cesta de prueba, y expone un objeto `hass` falso con callWS y
 * connection.subscribeMessage. El planificador usa el mismo generador aleatorio que el de
 * Python, así que con la misma semilla da el mismo menú (lo comprueban los tests). */
(function () {
  const D = (typeof window !== "undefined" ? window : globalThis).MENU_DATA;

  /* ------------------------------------------------------------ utilidades */
  const norm = (s) => String(s ?? "").normalize("NFKD").replace(/[̀-ͯ]/g, "").trim().toLowerCase().replace(/\s+/g, " ");
  const stem = (w) => {
    if (w.length > 3 && w.endsWith("s")) w = w.slice(0, -1);
    if (w.length > 3 && w.endsWith("e")) w = w.slice(0, -1);
    return w;
  };
  const stems = (t) => norm(t).split(/[^a-z0-9]+/).filter(Boolean).map(stem);
  const skey = (t) => stems(t).join(" ");
  const clean = (n, limit = 80) => {
    n = String(n ?? "").replace(/\s+/g, " ").trim().slice(0, limit);
    return n ? n[0].toUpperCase() + n.slice(1) : n;
  };
  const uid = () => Math.random().toString(16).slice(2, 14);
  const now = () => Math.round(Date.now()) / 1000;
  const err = (code, message) => Object.assign(new Error(message), { code });
  const copy = (x) => JSON.parse(JSON.stringify(x));
  const round1 = (v) => Math.trunc(v * 10 + 0.5) / 10;
  const roundInt = (v) => (v >= 0 ? Math.trunc(v + 0.5) : -Math.trunc(-v + 0.5));
  const clampNum = (value, low, high, dflt) => {
    if (value === null || value === undefined || value === "") return dflt;
    const n = Number(String(value).replace(",", "."));
    if (!Number.isFinite(n)) return dflt;
    return Math.max(low, Math.min(high, n));
  };

  /* ------------------------------------------------------------ catálogo */
  const CATALOG = D.catalog;
  const catIndex = new Map(CATALOG.map((e) => [norm(e.name), e]));
  const catStems = CATALOG.map((e) => [stems(e.name), e]);
  const catByStems = new Map();
  for (const [w, e] of catStems) if (!catByStems.has(w.join(" "))) catByStems.set(w.join(" "), e);
  const canonical = (name) => catIndex.get(norm(name)) || catByStems.get(skey(name)) || null;
  function guess(name) {
    const key = norm(name);
    if (catIndex.has(key)) return catIndex.get(key);
    const words = stems(name);
    if (!words.length) return null;
    let best = null;
    let bestScore = 0;
    for (const [cw, entry] of catStems) {
      if (!cw.length || cw.length > words.length) continue;
      for (let s = 0; s + cw.length <= words.length; s++) {
        if (cw.every((w, i) => words[s + i] === w)) {
          let score = cw.reduce((n, w) => n + w.length, 0) * 10 + (s === 0 ? 5 : 0);
          if (cw.length === words.length) score += 1000;
          if (score > bestScore) [best, bestScore] = [entry, score];
          break;
        }
      }
    }
    return best;
  }

  /* ------------------------------------------------------------ nutrición (nutrition.py) */
  const UNITS = D.units;
  const BASICS = new Set(D.basics);
  const PORTION_MIN = { legumbre: 50, pescado: 80, carne: 80 };
  const EGG_G = 55;
  const CATEGORY_OF_GROUP = {
    carne: ["carne", 2.0], carne_roja: ["carne", 2.0], procesada: ["carne", 1.5], pescado: ["pescado", 2.2],
    huevo: ["huevo", 2.2], legumbre: ["legumbre", 3.0], cereal: ["cereal", 1.4], tuberculo: ["cereal", 0.5], verdura: ["verdura", 1.0],
  };
  const foodIndex = new Map();
  const foodStemIndex = new Map();
  const foodStemList = [];
  for (const [names, kcal, protein, carbs, fat, group, unit_g, base] of D.foods) {
    const data = { name: names[0], kcal, protein, carbs, fat, group, unit_g, base };
    for (const n of names) {
      if (!foodIndex.has(norm(n))) foodIndex.set(norm(n), data);
      const w = stems(n);
      if (!foodStemIndex.has(w.join(" "))) foodStemIndex.set(w.join(" "), data);
      foodStemList.push([w, data]);
    }
  }
  const foodCache = new Map();
  function matchFood(name) {
    if (foodCache.has(name)) return foodCache.get(name);
    const res = (() => {
      const key = norm(name);
      if (!key) return null;
      if (foodIndex.has(key)) return foodIndex.get(key);
      const words = stems(name);
      if (!words.length) return null;
      const joined = words.join(" ");
      if (foodStemIndex.has(joined)) return foodStemIndex.get(joined);
      let best = null;
      let bestScore = 0;
      for (const [cand, data] of foodStemList) {
        const size = cand.length;
        if (size === 0 || size > words.length) continue;
        for (let start = 0; start + size <= words.length; start++) {
          if (cand.every((w, i) => words[start + i] === w)) {
            const score = cand.reduce((n, w) => n + w.length, 0) * 10 + (start === 0 ? 5 : 0);
            if (score > bestScore) [best, bestScore] = [data, score];
            break;
          }
        }
      }
      return best;
    })();
    foodCache.set(name, res);
    return res;
  }
  const unitInfo = (unit) => UNITS[unit || ""] || UNITS.g;
  function gramsOf(ing, food) {
    const info = unitInfo(ing.unit);
    if (info.kind === "any") return 0;
    if (ing.qty === null || ing.qty === undefined || ing.qty === "") return null;
    if (info.kind === "count") {
      if (!food || !food.unit_g) return null;
      return Number(ing.qty) * food.unit_g;
    }
    return Number(ing.qty) * info.factor;
  }
  function suggestCategory(groups) {
    const score = new Map();
    for (const [group, grams] of Object.entries(groups)) {
      if (CATEGORY_OF_GROUP[group]) {
        const [cat, w] = CATEGORY_OF_GROUP[group];
        score.set(cat, (score.get(cat) || 0) + grams * w);
      }
    }
    let best = "otros";
    let bestValue = 0;
    for (const [cat, v] of score) if (v > bestValue) [best, bestValue] = [cat, v];
    return best;
  }
  function analyze(recipe) {
    const servings = Math.max(1, Math.trunc(recipe.servings || 1));
    let kcal = 0, protein = 0, carbs = 0, fat = 0;
    const groups = {};
    const unknown = [];
    let known = 0;
    let bases = new Map();
    for (const ing of recipe.ingredients || []) {
      const name = String(ing.name || "").trim();
      if (!name) continue;
      const food = matchFood(name);
      const grams = gramsOf(ing, food);
      if (!food || grams === null) {
        if (unitInfo(ing.unit).kind !== "any") unknown.push(name);
        continue;
      }
      known += 1;
      const factor = grams / 100;
      kcal += food.kcal * factor;
      protein += food.protein * factor;
      carbs += food.carbs * factor;
      fat += food.fat * factor;
      groups[food.group] = (groups[food.group] || 0) + grams;
      if (food.base && grams >= 100) bases.set(norm(food.base), food.base);
    }
    const explicit = String(recipe.base || "").trim();
    if (explicit) bases = new Map([[norm(explicit), explicit], ...bases]);
    const per = {};
    for (const [g, v] of Object.entries(groups)) per[g] = round1(v / servings);
    const manual = recipe.kcal;
    const estimated = known ? round1(kcal / servings) : null;
    const g = (k) => per[k] || 0;
    return {
      kcal: manual ? Number(manual) : estimated,
      kcal_estimated: estimated,
      kcal_manual: !!manual,
      protein: known ? round1(protein / servings) : null,
      carbs: known ? round1(carbs / servings) : null,
      fat: known ? round1(fat / servings) : null,
      veg_g: g("verdura"),
      groups: per,
      unknown,
      known,
      suggested_category: suggestCategory(groups),
      bases: [...bases].map(([key, name]) => ({ key, name })),
      portions: {
        legumbre: g("legumbre") >= PORTION_MIN.legumbre,
        pescado: g("pescado") >= PORTION_MIN.pescado,
        carne: g("carne") + g("carne_roja") + g("procesada") >= PORTION_MIN.carne,
        huevos: round1(g("huevo") / EGG_G),
      },
      red_meat: g("carne_roja") >= 50,
      processed: g("procesada") >= 25,
    };
  }

  /* ------------------------------------------------------------ planificador (planner.py) */
  const SLOTS = 14;
  const LUNCH_SHARE = 0.35;
  const DINNER_SHARE = 0.3;
  const RATING_PREF = { 1: -3.0, 2: -1.0, 3: 1.0, 4: 2.5, 5: 4.0 };
  const RECENCY = {
    5: { 1: 2.5, 2: 0.5 },
    4: { 1: 4.0, 2: 1.5 },
    3: { 1: 5.0, 2: 2.5, 3: 1.0 },
    2: { 1: 7.0, 2: 5.0, 3: 3.0, 4: 1.0 },
    1: { 1: 10.0, 2: 8.0, 3: 6.0, 4: 4.0 },
  };
  const REPEAT = { 5: 3.5, 4: 6.0, 3: 12.0, 2: 12.0, 1: 12.0 };
  const WEEK_TARGETS = [
    { id: "legumbre", min: 4, max: null, weight: 5.0 },
    { id: "pescado", min: 3, max: 5, weight: 4.0 },
    { id: "carne", min: null, max: 3, weight: 4.0 },
    { id: "huevo", min: null, max: 4, weight: 1.5 },
    { id: "verdura", min: 2, max: null, weight: 2.0 },
    { id: "cereal", min: null, max: 4, weight: 1.0 },
  ];
  const MAX_RED = 1.5;
  const MAX_PROCESSED = 1.0;
  const DAY_PROTEIN = 35.0;
  const DAY_VEG = 250.0;
  const DAY_CARBS = 60.0;
  const MEAL_VEG = 40.0;
  const BATCH_BONUS = 1.5;
  const PANTRY_BONUS = 1.5;
  const RESTARTS = 6;
  const MAX_CANDIDATES = 20;
  const PASSES = 2;
  const RANK_WEIGHTS = [0.55, 0.25, 0.13, 0.07];
  const CHANGE_WEIGHTS = [0.6, 0.28, 0.12];
  const FREE = "free";

  function Rng(seed) {
    let a = seed | 0;
    this.random = () => {
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    this.below = (n) => Math.floor(this.random() * n);
  }

  function recipeCounts(cat, info) {
    const portions = info.known ? info.portions : null;
    let legume, fish, meat, eggs;
    if (portions) {
      legume = portions.legumbre ? 1.0 : 0.0;
      fish = portions.pescado ? 1.0 : 0.0;
      meat = portions.carne ? 1.0 : 0.0;
      eggs = Number(portions.huevos);
    } else {
      legume = cat === "legumbre" ? 1.0 : 0.0;
      fish = cat === "pescado" ? 1.0 : 0.0;
      meat = cat === "carne" ? 1.0 : 0.0;
      eggs = cat === "huevo" ? 2.0 : 0.0;
    }
    return { legumbre: legume, pescado: fish, carne: meat, huevo: eggs, verdura: cat === "verdura" ? 1.0 : 0.0, cereal: cat === "cereal" ? 1.0 : 0.0 };
  }

  function Cand(recipe, info, settings, weeksAgo, pantry, jitter) {
    this.id = recipe.id;
    this.recipe = recipe;
    this.meals = recipe.meals || [];
    this.cat = recipe.category || "otros";
    const rating = Math.trunc(recipe.rating || 3);
    this.rating = rating < 1 ? 1 : rating > 5 ? 5 : rating;
    this.known = !!info.known || !!info.kcal_manual;
    this.kcal = info.kcal ?? null;
    this.protein = info.protein !== null && info.protein !== undefined ? info.protein : 20.0;
    this.carbs = info.carbs !== null && info.carbs !== undefined ? info.carbs : 35.0;
    this.veg = info.known ? info.veg_g || 0.0 : 120.0;
    this.bases = (info.bases || []).map((b) => b.key);
    this.counts = recipeCounts(this.cat, info);
    this.red = !!info.red_meat;
    this.processed = !!info.processed;
    let recency = 0.0;
    if (weeksAgo !== undefined && weeksAgo !== null) recency = RECENCY[this.rating][weeksAgo] || 0.0;
    const bonus = settings.prefer_pantry ? PANTRY_BONUS * pantry : 0.0;
    this.base_score = RATING_PREF[this.rating] + jitter + bonus - recency;
  }

  class Context {
    constructor(recipes, infos, settings, history = {}, pantry = {}, seed = 1) {
      this.rng = new Rng(seed);
      this.settings = settings;
      this.batch = settings.batch !== undefined ? !!settings.batch : true;
      const kcalDay = Number(settings.kcal_day || 2000);
      this.t_lunch = kcalDay * LUNCH_SHARE;
      this.t_dinner = kcalDay * DINNER_SHARE;
      this.cands = [];
      for (const r of recipes) {
        const jitter = this.rng.random();
        this.cands.push(new Cand(r, infos[r.id], settings, history[r.id], pantry[r.id] || 0.0, jitter));
      }
      this.by_id = new Map(this.cands.map((c) => [c.id, c]));
      this.by_meal = [this.cands.filter((c) => c.meals.includes("lunch")), this.cands.filter((c) => c.meals.includes("dinner"))];
      this.planned = SLOTS;
    }

    score(assign) {
      let total = 0.0;
      const counts = { legumbre: 0.0, pescado: 0.0, carne: 0.0, huevo: 0.0, verdura: 0.0, cereal: 0.0 };
      const uses = new Map();
      const baseDays = new Map();
      const baseIds = new Map();
      let red = 0;
      let processed = 0;
      for (let s = 0; s < SLOTS; s++) {
        const r = assign[s];
        if (!r) continue;
        total += r.base_score;
        for (const [k, v] of Object.entries(r.counts)) counts[k] += v;
        if (uses.has(r.id)) uses.get(r.id).push(s);
        else uses.set(r.id, [s]);
        if (r.red) red += 1;
        if (r.processed) processed += 1;
        if (s >= 2) {
          const prev = assign[s - 2];
          if (prev && prev.cat === r.cat && r.cat !== "otros") total -= 0.75;
        }
        if (this.batch) {
          const day = Math.floor(s / 2);
          for (const key of r.bases) {
            const days = baseDays.get(key);
            if (!days) {
              baseDays.set(key, [day]);
              baseIds.set(key, [r.id]);
            } else {
              if (!days.includes(day)) days.push(day);
              if (!baseIds.get(key).includes(r.id)) baseIds.get(key).push(r.id);
            }
          }
        }
      }
      for (let d = 0; d < 7; d++) total -= this._dayPenalty(assign[2 * d], assign[2 * d + 1]);
      const f = this.planned / SLOTS;
      for (const t of WEEK_TARGETS) {
        const n = counts[t.id];
        if (t.min !== null && n < t.min * f) total -= t.weight * (t.min * f - n);
        if (t.max !== null && n > t.max * f) total -= t.weight * (n - t.max * f);
      }
      if (red > MAX_RED * f) total -= red - MAX_RED * f;
      if (processed > MAX_PROCESSED * f) total -= processed - MAX_PROCESSED * f;
      for (const [rid, slots] of uses) {
        const c = slots.length;
        if (c < 2) continue;
        const rating = this.by_id.get(rid).rating;
        total -= (c - 1) * REPEAT[rating];
        if (c > 2) total -= (c - 2) * 15.0;
        for (let i = 1; i < c; i++) {
          const gap = Math.floor(slots[i] / 2) - Math.floor(slots[i - 1] / 2);
          if (gap === 0) total -= 20.0;
          else if (gap === 1) total -= 3.0;
        }
      }
      if (this.batch) {
        for (const [key, days] of baseDays) if (days.length >= 2 && baseIds.get(key).length >= 2) total += BATCH_BONUS;
      }
      return total;
    }

    _dayPenalty(a, b) {
      let pen = 0.0, kcal = 0.0, protein = 0.0, veg = 0.0, carbs = 0.0;
      for (const [r, target] of [[a, this.t_lunch], [b, this.t_dinner]]) {
        if (!r) continue;
        const k = r.kcal !== null ? r.kcal : target;
        const dev = Math.abs(k - target) / target;
        if (dev > 0.25) pen += (dev - 0.25) * 3.0;
        kcal += k;
        protein += r.protein;
        veg += r.veg;
        carbs += r.carbs;
        if (r.known && r.veg < MEAL_VEG) pen += 0.5;
      }
      if (a && b) {
        const t = this.t_lunch + this.t_dinner;
        const dev = Math.abs(kcal - t) / t;
        if (dev > 0.1) pen += (dev - 0.1) * 6.0;
        if (protein < DAY_PROTEIN) pen += (DAY_PROTEIN - protein) * 0.08;
        if (veg < DAY_VEG) pen += (DAY_VEG - veg) * 0.012;
        if (carbs < DAY_CARBS) pen += (DAY_CARBS - carbs) * 0.03;
        if (a.cat === b.cat) pen += a.cat === "verdura" || a.cat === "otros" ? 1.0 : 2.0;
      }
      return pen;
    }

    _sample(cands, k) {
      const pool = [...cands];
      const n = pool.length;
      if (k > n) k = n;
      for (let i = 0; i < k; i++) {
        const j = i + this.rng.below(n - i);
        [pool[i], pool[j]] = [pool[j], pool[i]];
      }
      return pool.slice(0, k);
    }
    _shuffle(items) {
      for (let i = items.length - 1; i > 0; i--) {
        const j = this.rng.below(i + 1);
        [items[i], items[j]] = [items[j], items[i]];
      }
    }
    _rankPick(n, weights) {
      const size = n < weights.length ? n : weights.length;
      let total = 0.0;
      for (let i = 0; i < size; i++) total += weights[i];
      let x = this.rng.random() * total;
      for (let i = 0; i < size; i++) {
        x -= weights[i];
        if (x < 0) return i;
      }
      return size - 1;
    }
    _greedy(assign, fixed) {
      const order = [];
      for (let s = 0; s < SLOTS; s++) if (!fixed[s]) order.push(s);
      this._shuffle(order);
      for (const s of order) {
        const cands = this.by_meal[s % 2];
        if (!cands.length) continue;
        const scored = [];
        this._sample(cands, MAX_CANDIDATES).forEach((r, i) => {
          assign[s] = r;
          scored.push([this.score(assign), i, r]);
        });
        scored.sort((x, y) => y[0] - x[0] || x[1] - y[1]);
        assign[s] = scored[this._rankPick(scored.length, RANK_WEIGHTS)][2];
      }
    }
    _improve(assign, fixed) {
      let best = this.score(assign);
      for (let pass = 0; pass < PASSES; pass++) {
        let improved = false;
        for (let s = 0; s < SLOTS; s++) {
          if (fixed[s]) continue;
          let keep = assign[s];
          for (const r of this._sample(this.by_meal[s % 2], MAX_CANDIDATES)) {
            if (r === keep) continue;
            assign[s] = r;
            const value = this.score(assign);
            if (value > best + 1e-9) {
              best = value;
              keep = r;
              improved = true;
            }
          }
          assign[s] = keep;
        }
        for (let s1 = 0; s1 < SLOTS; s1++) {
          if (fixed[s1]) continue;
          for (let s2 = s1 + 1; s2 < SLOTS; s2++) {
            if (fixed[s2]) continue;
            const a = assign[s1];
            const b = assign[s2];
            if (!a || !b || a === b) continue;
            if (s1 % 2 !== s2 % 2 && (!b.meals.includes(s1 % 2 ? "dinner" : "lunch") || !a.meals.includes(s2 % 2 ? "dinner" : "lunch"))) continue;
            assign[s1] = b;
            assign[s2] = a;
            const value = this.score(assign);
            if (value > best + 1e-9) {
              best = value;
              improved = true;
            } else {
              assign[s1] = a;
              assign[s2] = b;
            }
          }
        }
        if (!improved) break;
      }
      return best;
    }
    generate(fixedSlots) {
      const base = [];
      const fixed = [];
      for (const v of fixedSlots) {
        if (v === null || v === undefined) {
          base.push(null);
          fixed.push(false);
        } else if (v === FREE) {
          base.push(null);
          fixed.push(true);
        } else {
          base.push(this.by_id.get(v) || null);
          fixed.push(true);
        }
      }
      this.planned = 0;
      for (let s = 0; s < SLOTS; s++) if (!(fixed[s] && base[s] === null)) this.planned += 1;
      let best = [...base];
      let bestValue = null;
      for (let k = 0; k < RESTARTS; k++) {
        const assign = [...base];
        this._greedy(assign, fixed);
        const value = this._improve(assign, fixed);
        if (bestValue === null || value > bestValue + 1e-9) {
          best = [...assign];
          bestValue = value;
        }
      }
      return best;
    }
    change(assignIds, slot, rejected) {
      const assign = assignIds.map((i) => (i ? this.by_id.get(i) || null : null));
      this.planned = assignIds.filter(Boolean).length;
      if (!assign[slot]) this.planned += 1;
      const cur = assign[slot];
      const meal = this.by_meal[slot % 2];
      let cands = meal.filter((r) => r !== cur && !rejected.includes(r.id));
      let restarted = false;
      if (!cands.length) {
        cands = meal.filter((r) => r !== cur);
        restarted = true;
      }
      if (!cands.length) return [null, restarted];
      const target = slot % 2 ? this.t_dinner : this.t_lunch;
      const scored = [];
      cands.forEach((r, i) => {
        assign[slot] = r;
        let value = this.score(assign);
        if (cur) {
          if (r.cat === cur.cat) value += 4.0;
          if (r.kcal !== null && cur.kcal !== null) {
            const diff = Math.abs(r.kcal - cur.kcal) / target;
            value -= 3.0 * (diff < 1 ? diff : 1.0);
          }
        }
        scored.push([value, i, r]);
      });
      scored.sort((x, y) => y[0] - x[0] || x[1] - y[1]);
      return [scored[this._rankPick(scored.length, CHANGE_WEIGHTS)][2], restarted];
    }
  }

  function weekTargets(planned) {
    const f = planned / SLOTS;
    return WEEK_TARGETS.map((t) => ({ id: t.id, min: t.min !== null ? roundInt(t.min * f) : null, max: t.max !== null ? roundInt(t.max * f) : null }));
  }

  function summarize(slots, recipes, infos, settings, baseAmounts) {
    const kcalDay = Number(settings.kcal_day || 2000);
    const targets = { lunch: kcalDay * LUNCH_SHARE, dinner: kcalDay * DINNER_SHARE };
    const days = [];
    const counts = {};
    const portions = { legumbre: 0.0, pescado: 0.0, carne: 0.0, huevo: 0.0, verdura: 0.0, cereal: 0.0 };
    let planned = 0;
    const groups = new Map();
    const cook = new Map();
    for (let d = 0; d < 7; d++) {
      const day = { kcal: 0.0, protein: 0.0, carbs: 0.0, fat: 0.0, veg: 0.0, meals: 0, unknown: false };
      ["lunch", "dinner"].forEach((meal, m) => {
        const slot = slots[2 * d + m];
        if (!slot || slot.free) return;
        planned += 1;
        const recipe = recipes.get(slot.recipe_id || "");
        if (!recipe) return;
        const info = infos[recipe.id];
        day.meals += 1;
        const cat = recipe.category || "otros";
        counts[cat] = (counts[cat] || 0) + 1;
        for (const [k, v] of Object.entries(recipeCounts(cat, info))) portions[k] += v;
        if (info.kcal === null || info.kcal === undefined) {
          day.unknown = true;
          day.kcal += targets[meal];
        } else day.kcal += info.kcal;
        for (const k of ["protein", "carbs", "fat"]) if (info[k] !== null && info[k] !== undefined) day[k] += info[k];
        day.veg += info.veg_g || 0.0;
        if (!cook.has(recipe.id)) cook.set(recipe.id, { recipe_id: recipe.id, slots: [] });
        cook.get(recipe.id).slots.push([d, meal]);
        for (const base of info.bases || []) {
          if (!groups.has(base.key)) groups.set(base.key, { key: base.key, name: base.name, slots: [], recipes: [] });
          const g = groups.get(base.key);
          g.slots.push([d, meal, recipe.id]);
          if (!g.recipes.includes(recipe.id)) g.recipes.push(recipe.id);
        }
      });
      for (const k of ["kcal", "protein", "carbs", "fat", "veg"]) day[k] = roundInt(day[k]);
      const full = day.meals === 2;
      day.target = roundInt(targets.lunch + targets.dinner);
      day.ok_protein = full ? day.protein >= DAY_PROTEIN : null;
      day.ok_veg = full ? day.veg >= DAY_VEG : null;
      day.ok_carbs = full ? day.carbs >= DAY_CARBS : null;
      days.push(day);
    }
    const batch = [];
    for (const [key, g] of groups) {
      const daySet = new Set(g.slots.map((s) => s[0]));
      if (g.recipes.length >= 2 && daySet.size >= 2) batch.push({ ...g, amount: (baseAmounts || {})[key] || null });
    }
    const weekly = weekTargets(planned).map((t) => {
      const n = round1(portions[t.id]);
      return { ...t, count: n, ok: (t.min === null || n >= t.min) && (t.max === null || n <= t.max) };
    });
    return {
      days, counts, weekly, batch, cook: [...cook.values()], planned,
      targets: { lunch: roundInt(targets.lunch), dinner: roundInt(targets.dinner) },
    };
  }

  /* ------------------------------------------------------------ despensa (pantry.py) */
  const LABEL_FACTORS = {
    g: [1, false], gr: [1, false], grs: [1, false], gramo: [1, false], gramos: [1, false],
    kg: [1000, false], kgs: [1000, false], kilo: [1000, false], kilos: [1000, false], kilogramo: [1000, false], kilogramos: [1000, false],
    ml: [1, true], cl: [10, true], l: [1000, true], lt: [1000, true], litro: [1000, true], litros: [1000, true],
  };
  const PIECE_LABELS = new Set(["", "u", "ud", "uds", "unidad", "unidades", "pieza", "piezas"]);
  const NOTE_WORDS = /^(?:x|u|uds?\.?|unidades?|latas?|botes?|bricks?|botellas?|paquetes?|cajas?|bolsas?|rollos?|piezas?|sobres?|tarros?|packs?)$/;
  const packageIndex = new Map();
  for (const [names, amount, label, volume] of D.packages) for (const n of names) packageIndex.set(skey(n), [amount, label, volume]);
  const packageFor = (name) => packageIndex.get(skey(name)) || null;
  const labelFactor = (label) => LABEL_FACTORS[norm(label || "").replace(/\.$/, "")] || null;
  const fmtNumber = (v) => (Math.abs(v - Math.round(v)) < 0.05 ? String(Math.round(v)) : v.toFixed(1).replace(".", ","));
  const fmtAmount = (g, volume = false) => (g >= 1000 ? `${fmtNumber(g / 1000)} ${volume ? "l" : "kg"}` : `${fmtNumber(g)} ${volume ? "ml" : "g"}`);
  function fmtUnits(count, label = "") {
    label = (label || "").trim();
    const n = fmtNumber(count);
    if (!label) return n === "1" ? `${n} ud` : `${n} uds`;
    if (n === "1" && label === "uds") return "1 ud";
    if (n === "1" && label.length > 3 && label.endsWith("s")) label = /[dlnzrj]es$/.test(label) && label.length > 4 ? label.slice(0, -2) : label.slice(0, -1);
    return `${n} ${label}`;
  }
  const ceil = (v) => Math.ceil(v - 1e-9);

  function matchItem(name, items) {
    const key = norm(name);
    if (!key) return null;
    let found = items.find((i) => norm(i.name) === key);
    if (found) return found;
    const words = stems(name);
    found = items.find((i) => skey(i.name) === words.join(" "));
    if (found) return found;
    const canon = canonical(name);
    if (canon) {
      found = items.find((i) => norm(i.name) === norm(canon.name));
      if (found) return found;
    }
    if (!words.length) return null;
    const contains = (hay, needle) => hay.some((_, i) => needle.length && needle.every((w, j) => hay[i + j] === w));
    let wider = items.filter((i) => contains(stems(i.name), words));
    if (wider.length > 1) {
      const stocked = wider.filter((i) => (i.stock || 0) > 0);
      if (stocked.length >= 1) wider = stocked;
      wider.sort((a, b) => a.name.length - b.name.length || norm(a.name).localeCompare(norm(b.name)));
    }
    if (wider.length) return wider[0];
    const narrower = items.filter((i) => stems(i.name).length && contains(words, stems(i.name)));
    if (narrower.length) return narrower.reduce((a, b) => (stems(b.name).length > stems(a.name).length ? b : a));
    return null;
  }
  function unitSize(item, equivalences) {
    const factor = labelFactor(item.unit);
    if (factor) return [factor[0], factor[1], "label"];
    const eq = equivalences[norm(item.name)];
    if (eq && eq.grams) return [Number(eq.grams), !!eq.volume, "user"];
    const pkg = packageFor(item.name);
    if (pkg) return [pkg[0], pkg[2], "default"];
    const label = norm(item.unit || "").replace(/\.$/, "");
    const food = matchFood(item.name);
    if (food && food.unit_g && PIECE_LABELS.has(label)) return [food.unit_g, false, "piece"];
    return [null, false, ""];
  }
  function pantryRatio(recipe, items) {
    let total = 0;
    let have = 0;
    for (const ing of recipe.ingredients || []) {
      const name = String(ing.name || "");
      if (!name || BASICS.has(norm(name))) continue;
      total += 1;
      const item = matchItem(name, items);
      if (item && (item.stock || 0) > 0) have += 1;
    }
    return total ? have / total : 0.0;
  }
  function checkPantry(lines, items, inCesta, equivalences) {
    const pantry = items || [];
    const groups = new Map();
    for (const line of lines) {
      const name = String(line.name || "").trim();
      if (!name || norm(name) === "agua") continue;
      const item = items ? matchItem(name, pantry) : null;
      let key, display;
      if (item) {
        key = `item:${item.id}`;
        display = item.name;
      } else {
        const canon = canonical(name);
        display = canon ? canon.name : name[0].toUpperCase() + name.slice(1);
        key = `name:${skey(display)}`;
      }
      if (!groups.has(key)) groups.set(key, { key, name: display, item, lines: [] });
      groups.get(key).lines.push(line);
    }
    const order = { missing: 0, unsure: 1, in_cesta: 2, ok: 3, untracked: 4 };
    return [...groups.values()]
      .map((g) => evaluate(g, inCesta, equivalences))
      .sort((a, b) => order[a.status] - order[b.status] || norm(a.name).localeCompare(norm(b.name)));
  }
  function evaluate(group, inCesta, equivalences) {
    const item = group.item;
    const name = group.name;
    let mass = 0.0, count = 0.0, countMass = 0.0, countKnown = true, anyOnly = true, volumeLines = 0, massLines = 0;
    for (const line of group.lines) {
      const info = unitInfo(line.unit);
      if (info.kind === "any" || line.qty === null || line.qty === undefined) continue;
      anyOnly = false;
      if (info.kind === "count") {
        count += Number(line.qty);
        const food = matchFood(line.name);
        if (food && food.unit_g) countMass += Number(line.qty) * food.unit_g;
        else countKnown = false;
      } else {
        mass += Number(line.qty) * info.factor;
        massLines += 1;
        if (line.unit === "ml" || line.unit === "l") volumeLines += 1;
      }
    }
    const volume = massLines > 0 && volumeLines === massLines;
    const basic = BASICS.has(norm(name)) || group.lines.some((l) => BASICS.has(norm(l.name)));
    const pkg = packageFor(name);
    const canon = guess(name);
    const out = {
      key: group.key, name,
      icon: (item && item.icon) || (canon ? canon.icon : "🛒"),
      department: (item && item.department) || (canon ? canon.department : "otros"),
      item_id: item ? item.id : null, stock: item ? item.stock : null, unit_label: (item && item.unit) || "",
      recipes: group.lines.map((l) => ({ recipe_id: l.recipe_id, recipe: l.recipe, day: l.day, meal: l.meal })),
      need_text: "", have_text: null, missing: 0, note: "", equivalence: null, status: "ok",
    };
    if (anyOnly) out.need_text = "al gusto";
    else if (mass && count) out.need_text = fmtAmount(countKnown ? mass + countMass : mass, volume) + (countKnown ? "" : ` + ${fmtUnits(count)}`);
    else if (mass) out.need_text = fmtAmount(mass, volume);
    else out.need_text = fmtUnits(count);
    const cesta = (o) => {
      if (o.status === "missing" && inCesta.has(skey(o.name))) o.status = "in_cesta";
      return o;
    };
    if (!item) {
      if (basic) {
        out.status = "untracked";
        return out;
      }
      out.status = "missing";
      if (anyOnly) out.missing = 1;
      else if (pkg && (mass || countKnown)) {
        const total = mass + countMass;
        let n = total > 0 ? ceil(total / pkg[0]) : 1;
        if (!mass && count && pkg[1] === "uds") n = ceil(count);
        out.missing = n;
        out.note = fmtUnits(n, pkg[1]);
      } else if (mass && !count) {
        out.missing = 1;
        out.note = fmtAmount(mass, volume);
      } else if (count && !mass) {
        out.missing = ceil(count);
        out.note = fmtUnits(ceil(count));
      } else {
        out.missing = 1;
        out.note = out.need_text;
      }
      return cesta(out);
    }
    const stock = Number(item.stock || 0);
    const label = item.unit || "";
    const [size, sizeVolume, origin] = unitSize(item, equivalences);
    out.equivalence = { grams: size, volume: sizeVolume || volume, origin };
    const unitText = label ? fmtUnits(stock, label) : stock !== 1 ? fmtUnits(stock) : "1 ud";
    out.have_text = unitText;
    if (size && origin !== "label") out.have_text = stock ? `${unitText} (≈ ${fmtAmount(stock * size, sizeVolume || volume)})` : unitText;
    const noteFor = (n) => {
      if (labelFactor(label)) return fmtUnits(n, label);
      if (label && NOTE_WORDS.test(norm(label))) return fmtUnits(n, label);
      if (!label && pkg) return fmtUnits(n, pkg[1]);
      return fmtUnits(n);
    };
    if (anyOnly) {
      if (stock <= 0) Object.assign(out, { status: "missing", missing: 1, note: noteFor(1) });
      return cesta(out);
    }
    if (!mass) {
      let missing;
      if (!labelFactor(label)) missing = ceil(count - stock);
      else if (countKnown) missing = size ? ceil((countMass - stock * size) / size) : 0;
      else {
        out.status = stock > 0 ? "unsure" : "missing";
        out.missing = stock > 0 ? 0 : 1;
        out.note = stock <= 0 ? noteFor(1) : "";
        return cesta(out);
      }
      if (missing > 0) Object.assign(out, { status: "missing", missing, note: noteFor(missing) });
      return cesta(out);
    }
    const needMass = mass + countMass;
    if (size === null || (count && !countKnown)) {
      out.status = stock > 0 ? "unsure" : "missing";
      if (stock <= 0) Object.assign(out, { missing: 1, note: fmtAmount(needMass, volume) });
      out.equivalence = { grams: null, volume, origin: "" };
      return cesta(out);
    }
    const missing = ceil((needMass - stock * size) / size);
    if (missing > 0) Object.assign(out, { status: "missing", missing, note: noteFor(missing) });
    return cesta(out);
  }

  /* ------------------------------------------------------------ semanas */
  const DAY_MS = 86400000;
  const todayISO = () => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  };
  const parseDay = (iso) => {
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(Date.UTC(y, m - 1, d));
  };
  const mondayOf = (key) => {
    const m = /^(\d{4})-W(\d{2})$/.exec(key);
    const jan4 = new Date(Date.UTC(+m[1], 0, 4));
    return new Date(jan4.getTime() + ((+m[2] - 1) * 7 - ((jan4.getUTCDay() + 6) % 7)) * DAY_MS);
  };
  const weekOf = (date) => {
    const thu = new Date(date.getTime() + (3 - ((date.getUTCDay() + 6) % 7)) * DAY_MS);
    const y = thu.getUTCFullYear();
    const jan4 = new Date(Date.UTC(y, 0, 4));
    const mon1 = jan4.getTime() - ((jan4.getUTCDay() + 6) % 7) * DAY_MS;
    return `${y}-W${String(Math.floor((thu.getTime() - mon1) / (7 * DAY_MS)) + 1).padStart(2, "0")}`;
  };
  const shiftWeek = (key, n) => weekOf(new Date(mondayOf(key).getTime() + n * 7 * DAY_MS));
  const currentWeek = () => weekOf(parseDay(todayISO()));
  const emptySlot = () => ({ recipe_id: null, free: false, locked: false, rejected: [] });

  /* ------------------------------------------------------------ estado */
  const MEALS = ["lunch", "dinner"];
  const MEAL_NAMES = { lunch: "Comida", dinner: "Cena" };
  const DEFAULT_SETTINGS = { ...D.settings, prefer_pantry: true };
  const PANTRY_SEED = [
    // nombre, stock, unidad (el icono y la balda salen del catálogo)
    ["Lentejas", 1, ""], ["Garbanzos", 2, ""], ["Alubias", 1, ""], ["Arroz", 2, ""], ["Espaguetis", 1, ""], ["Pasta", 2, ""],
    ["Cuscús", 1, ""], ["Quinoa", 1, ""], ["Tomate triturado", 3, "latas"], ["Tomate frito", 1, "botes"], ["Atún en lata", 4, "latas"],
    ["Aceite de oliva", 1, ""], ["Caldo", 2, "bricks"], ["Pan rallado", 1, ""], ["Harina", 1, ""],
    ["Huevos", 12, ""], ["Leche", 4, "bricks"], ["Queso rallado", 1, ""], ["Yogur griego", 2, ""],
    ["Patatas", 3, "kg"], ["Cebollas", 6, ""], ["Ajos", 12, ""], ["Zanahorias", 6, ""], ["Pimientos", 4, ""], ["Calabacines", 3, ""],
    ["Tomates", 6, ""], ["Limones", 2, ""], ["Lechuga", 0, ""], ["Espinacas", 1, "bolsas"],
    ["Carne picada", 0, ""], ["Pechugas de pollo", 2, ""], ["Salmón", 1, "bandejas"], ["Merluza", 0, ""],
  ];
  const DEMO_SEEDS = [3, 13];
  let state;
  const listeners = new Set();
  const cestaListeners = new Set();
  const pantryListeners = new Set();
  const infos = {};

  function makeRecipe(payload, existing) {
    const name = clean(payload.name);
    if (!name) throw err("invalid_name", "La receta necesita un nombre");
    const other = state.recipes.find((r) => norm(r.name) === norm(name) || skey(r.name) === skey(name));
    if (other && (!existing || other.id !== existing.id)) throw err("duplicate", `Ya tienes una receta llamada «${other.name}»`);
    const meals = MEALS.filter((m) => (payload.meals || []).includes(m));
    if (!meals.length) throw err("meals_required", "Elige si la receta es para comidas, para cenas o para las dos");
    const ingredients = [];
    for (const raw of (payload.ingredients || []).slice(0, 40)) {
      const n = clean((raw || {}).name);
      if (!n) continue;
      const unit = UNITS[raw.unit] ? raw.unit : "g";
      let qty = unit === "gusto" ? null : clampNum(raw.qty, 0, 100000, null);
      if (qty !== null) qty = Math.round(qty * 100) / 100;
      ingredients.push({ name: n, qty, unit });
    }
    const recipe = {
      id: existing ? existing.id : uid(),
      name,
      icon: String(payload.icon || "").trim().slice(0, 16),
      meals,
      category: D.categories.some((c) => c.id === payload.category) ? payload.category : null,
      rating: Math.trunc(clampNum(payload.rating, 1, 5, 3)),
      servings: Math.trunc(clampNum(payload.servings, 1, 20, 4)),
      ingredients,
      base: clean(payload.base, 40),
      kcal: null,
      notes: String(payload.notes || "").trim().slice(0, 4000),
      created_at: existing ? existing.created_at : now(),
      updated_at: now(),
    };
    const kcal = clampNum(payload.kcal, 0, 3000, null);
    recipe.kcal = kcal ? Math.trunc(kcal) : null;
    if (!recipe.category) recipe.category = analyze(recipe).suggested_category;
    if (!recipe.icon) recipe.icon = (D.categories.find((c) => c.id === recipe.category) || { icon: "🍽️" }).icon;
    return recipe;
  }

  function weekOfState(key, create) {
    let w = state.weeks[key];
    if (!w && create) w = state.weeks[key] = { slots: Array.from({ length: 14 }, emptySlot), generated_at: null };
    return w;
  }
  const slotsOf = (key) => (state.weeks[key] ? copy(state.weeks[key].slots) : Array.from({ length: 14 }, emptySlot));
  function history(key) {
    const h = {};
    for (let ago = 4; ago >= 1; ago--) {
      const w = state.weeks[shiftWeek(key, -ago)];
      if (!w) continue;
      for (const s of w.slots) if (s.recipe_id) h[s.recipe_id] = ago;
    }
    return h;
  }
  function context(key, seed) {
    const pantry = {};
    if (state.settings.prefer_pantry) for (const r of state.recipes) pantry[r.id] = pantryRatio(r, state.pantry);
    return new Context(copy(state.recipes), copy(infos), { ...state.settings }, history(key), pantry, seed || Math.floor(Math.random() * 2 ** 31) || 1);
  }
  function generate(key, seed) {
    if (!state.recipes.length) throw err("no_recipes", "Primero crea algunas recetas");
    const previous = slotsOf(key);
    const fixed = previous.map((s) => (s.free ? FREE : s.locked && s.recipe_id ? s.recipe_id : null));
    const ctx = context(key, seed);
    const result = ctx.generate(fixed);
    const week = weekOfState(key, true);
    week.slots = result.map((c, i) => {
      const old = week.slots[i];
      if (old.free) return { ...old };
      if (old.locked && old.recipe_id && ctx.by_id.has(old.recipe_id)) return { ...old, rejected: [] };
      return { recipe_id: c ? c.id : null, free: false, locked: false, rejected: [] };
    });
    week.generated_at = now();
    return { previous, slots: copy(week.slots) };
  }
  function change(key, index) {
    const week = weekOfState(key, true);
    const slot = week.slots[index];
    const previous = { ...slot };
    const ids = week.slots.map((s) => (s.free ? null : s.recipe_id));
    let rejected = [...(slot.rejected || [])];
    if (slot.recipe_id && !rejected.includes(slot.recipe_id)) rejected.push(slot.recipe_id);
    const [cand, restarted] = context(key).change(ids, index, rejected);
    if (!cand) throw err("no_alternative", `No hay otra receta para la ${MEAL_NAMES[MEALS[index % 2]].toLowerCase()}`);
    if (restarted) rejected = slot.recipe_id ? [slot.recipe_id] : [];
    week.slots[index] = { recipe_id: cand.id, free: false, locked: !!previous.locked, rejected };
    return { previous, slot: { ...week.slots[index] }, restarted };
  }
  function lines(key) {
    const monday = mondayOf(key);
    const today = parseDay(todayISO());
    let fromDay = 0;
    if (monday <= today && today < new Date(monday.getTime() + 7 * DAY_MS)) fromDay = Math.round((today - monday) / DAY_MS);
    else if (new Date(monday.getTime() + 7 * DAY_MS) <= today) fromDay = 7;
    const people = state.settings.people;
    const out = [];
    slotsOf(key).forEach((slot, index) => {
      const day = Math.floor(index / 2);
      if (day < fromDay || slot.free || !slot.recipe_id) return;
      const recipe = state.recipes.find((r) => r.id === slot.recipe_id);
      if (!recipe) return;
      const factor = people / Math.max(1, recipe.servings || 1);
      for (const ing of recipe.ingredients)
        out.push({ name: ing.name, qty: ing.qty === null ? null : Math.round(ing.qty * factor * 100) / 100, unit: ing.unit || "g", recipe_id: recipe.id, recipe: recipe.name, day, meal: MEALS[index % 2] });
    });
    return [out, fromDay];
  }
  function baseAmounts(slots) {
    const people = state.settings.people;
    const amounts = {};
    for (const slot of slots) {
      const recipe = state.recipes.find((r) => r.id === slot.recipe_id);
      if (!recipe || slot.free) continue;
      const factor = people / Math.max(1, recipe.servings || 1);
      for (const ing of recipe.ingredients) {
        const food = matchFood(ing.name);
        if (!food || !food.base) continue;
        const grams = gramsOf(ing, food);
        if (!grams) continue;
        const key = norm(food.base);
        amounts[key] = amounts[key] || { grams: 0 };
        amounts[key].grams = Math.round(amounts[key].grams + grams * factor);
      }
    }
    return amounts;
  }
  function weekSnapshot(key) {
    const slots = slotsOf(key);
    const w = state.weeks[key] || {};
    return {
      key,
      monday: mondayOf(key).toISOString().slice(0, 10),
      slots,
      generated_at: w.generated_at || null,
      summary: summarize(slots, new Map(state.recipes.map((r) => [r.id, r])), infos, state.settings, baseAmounts(slots)),
    };
  }
  function snapshot() {
    const cur = currentWeek();
    const keys = [...new Set([...Object.keys(state.weeks), cur, shiftWeek(cur, 1)])].sort();
    const weeks = {};
    for (const k of keys) weeks[k] = weekSnapshot(k);
    return {
      recipes: state.recipes.map((r) => ({ ...copy(r), info: copy(infos[r.id]) })),
      weeks,
      settings: { ...state.settings },
      categories: D.categories.map((c) => ({ ...c, color: state.colors[c.id] || c.color })),
      equivalences: Object.values(state.equivalences).sort((a, b) => norm(a.name).localeCompare(norm(b.name))),
      today: todayISO(),
      current_week: cur,
      despensa: { available: true, items: state.pantry.map((i) => ({ id: i.id, name: i.name, icon: i.icon, unit: i.unit, stock: i.stock, department: i.department })) },
      cesta: { available: true },
    };
  }
  function changed() {
    const snap = snapshot();
    for (const fn of listeners) fn(snap);
    for (const fn of cestaListeners) fn(copy(state.cesta));
    for (const fn of pantryListeners) fn(copy(state.pantry));
  }

  function pantryItem(name, stock, unit) {
    const c = canonical(name) || guess(name) || { icon: "🛒", department: "otros" };
    return { id: uid(), name, stock, unit, icon: c.icon, department: c.department };
  }

  function reset(prevSeed = DEMO_SEEDS[0], curSeed = DEMO_SEEDS[1]) {
    state = {
      recipes: [],
      weeks: {},
      settings: { ...DEFAULT_SETTINGS },
      equivalences: {},
      colors: {},
      pantry: PANTRY_SEED.map(([n, s, u]) => pantryItem(n, s, u)),
      cesta: [],
      deleted: {},
    };
    for (const k of Object.keys(infos)) delete infos[k];
    for (const ex of D.examples) {
      const r = makeRecipe({ ...copy(ex), servings: 4 }, null);
      state.recipes.push(r);
      infos[r.id] = analyze(r);
    }
    // La semana pasada (para que "no repetir" se note) y esta, ya generadas
    const cur = currentWeek();
    generate(shiftWeek(cur, -1), prevSeed);
    generate(cur, curSeed);
    changed();
  }

  /* ------------------------------------------------------------ API websocket */
  const handlers = {
    "menu_semanal/catalog": () => ({ catalog: CATALOG, foods: D.foods.map((e) => ({ name: e[0][0], group: e[5] })), units: UNITS }),
    "menu_semanal/recipe/save": (m) => {
      const existing = m.recipe_id ? state.recipes.find((r) => r.id === m.recipe_id) : null;
      if (m.recipe_id && !existing) throw err("not_found", "Esa receta ya no existe");
      const recipe = makeRecipe(m, existing);
      if (existing) Object.assign(existing, recipe);
      else state.recipes.push(recipe);
      infos[recipe.id] = analyze(recipe);
      return { recipe, info: infos[recipe.id] };
    },
    "menu_semanal/recipe/delete": (m) => {
      const recipe = state.recipes.find((r) => r.id === m.recipe_id);
      if (!recipe) throw err("not_found", "Esa receta ya no existe");
      state.recipes = state.recipes.filter((r) => r !== recipe);
      const cur = currentWeek();
      const removed = [];
      for (const [key, week] of Object.entries(state.weeks)) {
        if (key < cur) continue;
        week.slots.forEach((s, i) => {
          if (s.recipe_id === recipe.id) {
            removed.push([key, i, { ...s }]);
            week.slots[i] = emptySlot();
          }
        });
      }
      state.deleted = { [recipe.id]: [recipe, removed] };
      return { recipe };
    },
    "menu_semanal/recipe/restore": (m) => {
      const entry = state.deleted[m.recipe_id];
      if (!entry) throw err("not_found", "Ya no se puede recuperar");
      delete state.deleted[m.recipe_id];
      const [recipe, removed] = entry;
      state.recipes.push(recipe);
      infos[recipe.id] = analyze(recipe);
      for (const [key, i, slot] of removed) if (state.weeks[key] && !state.weeks[key].slots[i].recipe_id) state.weeks[key].slots[i] = slot;
      return { recipe };
    },
    "menu_semanal/recipe/estimate": (m) =>
      analyze({
        servings: Math.trunc(clampNum(m.servings, 1, 20, 4)),
        ingredients: (m.ingredients || []).map((i) => ({ name: String(i.name || ""), qty: clampNum(i.qty, 0, 100000, null), unit: UNITS[i.unit] ? i.unit : "g" })),
        base: m.base || "",
        kcal: clampNum(m.kcal, 0, 3000, null),
      }),
    "menu_semanal/recipes/examples": () => {
      let added = 0;
      for (const ex of D.examples) {
        if (state.recipes.some((r) => norm(r.name) === norm(ex.name))) continue;
        const r = makeRecipe({ ...copy(ex), servings: 4 }, null);
        state.recipes.push(r);
        infos[r.id] = analyze(r);
        added += 1;
      }
      return { added };
    },
    "menu_semanal/week/generate": (m) => generate(m.week, m.seed),
    "menu_semanal/slot/change": (m) => change(m.week, m.slot),
    "menu_semanal/slot/set": (m) => {
      if (m.recipe_id) {
        const r = state.recipes.find((x) => x.id === m.recipe_id);
        if (!r) throw err("not_found", "Esa receta ya no existe");
        const meal = MEALS[m.slot % 2];
        if (!r.meals.includes(meal)) throw err("wrong_meal", `«${r.name}» no está marcada para la ${MEAL_NAMES[meal].toLowerCase()}`);
      }
      const week = weekOfState(m.week, true);
      const previous = { ...week.slots[m.slot] };
      if (m.free) week.slots[m.slot] = { recipe_id: null, free: true, locked: false, rejected: [] };
      else if (m.recipe_id) week.slots[m.slot] = { recipe_id: m.recipe_id, free: false, locked: true, rejected: [] };
      else week.slots[m.slot] = emptySlot();
      return { previous };
    },
    "menu_semanal/slot/lock": (m) => {
      const s = weekOfState(m.week, true).slots[m.slot];
      if (!s.recipe_id) throw err("empty_slot", "No hay ningún plato que fijar");
      s.locked = !!m.locked;
      return null;
    },
    "menu_semanal/week/restore": (m) => {
      const known = new Set(state.recipes.map((r) => r.id));
      weekOfState(m.week, true).slots = m.slots.map((s) => ({
        recipe_id: known.has(s.recipe_id) ? s.recipe_id : null,
        free: !!s.free,
        locked: !!s.locked && known.has(s.recipe_id),
        rejected: (s.rejected || []).filter((r) => known.has(r)),
      }));
      return null;
    },
    "menu_semanal/week/clear": (m) => {
      const previous = slotsOf(m.week);
      delete state.weeks[m.week];
      return { previous };
    },
    "menu_semanal/check": (m) => {
      const [ls, fromDay] = lines(m.week);
      const items = checkPantry(ls, state.pantry, new Set(state.cesta.map((i) => skey(i.name))), state.equivalences);
      return { week: m.week, from_day: fromDay, people: state.settings.people, despensa: true, cesta: true, items, missing: items.filter((i) => i.status === "missing").length };
    },
    "menu_semanal/cesta/add": (m) => {
      const added = [];
      for (const e of m.items) {
        const name = String(e.name || "").trim();
        if (!name || state.cesta.some((i) => skey(i.name) === skey(name))) continue;
        const c = canonical(name) || guess(name) || {};
        state.cesta.push({ id: uid(), name, note: e.note || "", icon: e.icon || c.icon || "🛒", department: e.department || c.department || "otros" });
        added.push(name);
      }
      return { added };
    },
    "menu_semanal/settings/set": (m) => {
      if (m.people !== undefined) state.settings.people = Math.trunc(clampNum(m.people, 1, 12, 2));
      if (m.kcal_day !== undefined) state.settings.kcal_day = Math.trunc(clampNum(m.kcal_day, 1000, 4500, 2000));
      for (const k of ["batch", "prefer_pantry"]) if (m[k] !== undefined) state.settings[k] = !!m[k];
      return null;
    },
    "menu_semanal/category/color": (m) => {
      const def = D.categories.find((c) => c.id === m.category);
      if (!def) throw err("invalid_category", "Tipo de plato no válido");
      if (m.color && !/^#[0-9a-f]{6}$/i.test(m.color)) throw err("invalid_color", "Color no válido");
      if (!m.color || m.color.toLowerCase() === def.color.toLowerCase()) delete state.colors[m.category];
      else state.colors[m.category] = m.color;
      return null;
    },
    "menu_semanal/equivalence/set": (m) => {
      const key = norm(m.name);
      if (!m.grams) delete state.equivalences[key];
      else state.equivalences[key] = { name: clean(m.name), grams: Math.round(Number(m.grams) * 10) / 10, volume: !!m.volume };
      return null;
    },
  };

  const READ_ONLY = new Set(["menu_semanal/catalog", "menu_semanal/recipe/estimate", "menu_semanal/check"]);
  const hass = {
    language: "es",
    dockedSidebar: "docked",
    async callWS(msg) {
      await new Promise((r) => setTimeout(r, msg.type.endsWith("generate") ? 380 : msg.type.endsWith("change") ? 220 : 30));
      const fn = handlers[msg.type];
      if (!fn) throw err("unknown_command", `Comando desconocido: ${msg.type}`);
      const res = fn(msg);
      if (!READ_ONLY.has(msg.type)) changed();
      return copy(res);
    },
    connection: {
      async subscribeMessage(cb, msg) {
        if (msg.type !== "menu_semanal/subscribe") throw err("unknown_command", msg.type);
        listeners.add(cb);
        setTimeout(() => cb(snapshot()), 0);
        return () => listeners.delete(cb);
      },
    },
  };

  const backend = {
    reset,
    subscribeCesta(fn) {
      cestaListeners.add(fn);
      fn(copy(state.cesta));
    },
    subscribePantry(fn) {
      pantryListeners.add(fn);
      fn(copy(state.pantry));
    },
    /* "Comprado" en la Cesta: como la Despensa real, suma las unidades del detalle ("2 paquetes" → 2) */
    cestaPurchase(id) {
      const item = state.cesta.find((i) => i.id === id);
      if (!item) return;
      state.cesta = state.cesta.filter((i) => i !== item);
      const m = /^(?:pack\s+de\s+|x\s*)?(\d{1,3})\s*(?:x|u|uds?\.?|unidades?|latas?|botes?|bricks?|botellas?|paquetes?|cajas?|bolsas?|rollos?|piezas?|sobres?|tarros?|packs?)?$/.exec(norm(item.note));
      const qty = m ? Number(m[1]) : 1;
      const existing = matchItem(item.name, state.pantry);
      if (existing && skey(existing.name) === skey(item.name)) existing.stock += qty;
      else state.pantry.push({ id: uid(), name: item.name, stock: qty, unit: "", icon: item.icon, department: item.department });
      changed();
    },
    pantryAdjust(id, delta) {
      const item = state.pantry.find((i) => i.id === id);
      if (!item) return;
      item.stock = Math.max(0, item.stock + delta);
      changed();
    },
  };

  reset();
  const api = { hass, backend, _internals: { analyze, Context, summarize, checkPantry, Rng, snapshot, currentWeek } };
  if (typeof window !== "undefined") window.MenuDemo = api;
  else globalThis.MenuDemo = api;
})();

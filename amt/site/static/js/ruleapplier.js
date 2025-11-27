/**
 * Declarative Rule Application System
 * Applies CSS-like selector rules with actions to DOM elements
 *
 * USAGE
 * =====
 *
 * Basic Usage:
 * ------------
 * <button onclick="window.applyRules('self: +active', event)">Click</button>
 *
 * Multiple Rules (separated by semicolon):
 * ----------------------------------------
 * applyRules('self: +active; siblings: -active', event)
 *
 * Options:
 * --------
 * applyRules('self: +active', event, { preventDefault: true, stopPropagation: true })
 *
 * SELECTORS
 * =========
 *
 * Special Selectors:
 *   self              - The clicked element itself
 *   siblings          - All sibling elements
 *   parent            - Direct parent element
 *
 * Combined Selectors (NEW!):
 *   self > a          - Direct child <a> elements of clicked element
 *   self .active      - Descendant elements with class 'active'
 *   parent > div      - Direct child divs of parent
 *   siblings button   - All buttons within sibling elements
 *
 * CSS Combinators:
 *   ~ selector        - Following siblings (general sibling combinator)
 *   + selector        - Next sibling (adjacent sibling combinator)
 *   > selector        - Direct children (child combinator)
 *   ^ selector        - Closest parent matching selector (traverse up)
 *
 * Standard CSS:
 *   #id               - ID selector
 *   .class            - Class selector
 *   [attr="value"]    - Attribute selector
 *
 * Variable Interpolation:
 *   {data-target}     - Interpolate from data-target attribute
 *   {id}              - Interpolate element's id
 *   {attr:href}       - Interpolate from href attribute
 *
 * ACTIONS
 * =======
 *
 * Class Operations:
 *   +classname        - Add a single class
 *   -classname        - Remove a single class
 *   +[c1,c2,c3]       - Add multiple classes
 *   -[c1,c2,c3]       - Remove multiple classes
 *
 * Attribute Operations:
 *   attr=value        - Set attribute to value
 *   aria-selected=true
 *   data-active=1
 *
 * EXAMPLES
 * ========
 *
 * Tab Navigation (direct child links):
 * --------------------------------------
 * <li onclick="window.applyRules('self > a: +active; siblings > a: -active', event)">
 *   <a href="#">Tab 1</a>
 * </li>
 *
 * Tab Navigation (simple):
 * ------------------------
 * <button onclick="window.applyRules('self: +active aria-selected=true; siblings: -active aria-selected=false', event)">
 *   Tab 1
 * </button>
 *
 * Toggle Dropdown:
 * ----------------
 * <button onclick="window.applyRules('#{data-target}: +[visible,open]', event)">
 *   Toggle Menu
 * </button>
 *
 * Accordion:
 * ----------
 * <button onclick="window.applyRules('+ .content: +expanded; ~ button + .content: -expanded', event)">
 *   Section 1
 * </button>
 *
 * Radio Button Behavior:
 * ----------------------
 * <div onclick="window.applyRules('self: +selected; siblings: -selected', event)">
 *   Option 1
 * </div>
 *
 * Form Control:
 * -------------
 * <button onclick="window.applyRules('^form: +submitted', event, { preventDefault: true })">
 *   Submit
 * </button>
 */

class RuleApplier {
  constructor() {
    // Supported selector patterns and their descriptions
    this.supportedSelectors = {
      'self': 'The clicked element itself',
      'siblings': 'All sibling elements',
      'parent': 'Direct parent element',
      '~': 'Following siblings (CSS general sibling)',
      '+': 'Next sibling (CSS adjacent)',
      '>': 'Direct children (CSS child combinator)',
      '^': 'Traverse up to nearest matching parent',
      '#': 'ID selector or interpolation',
      '.': 'Class selector',
      '[': 'Attribute selector'
    };
    this.debug = true;
  }

  /**
   * Main entry point - applies rules from a click event
   */
  applyRules(rulesString, clickedElement) {
    try {
      const rules = this.parseRules(rulesString);
      this.executeRules(rules, clickedElement);
    } catch (error) {
      console.error('Rule application failed:', error.message);
      throw error;
    }
  }

  /**
   * Parse the rules string into structured rule objects
   */
  parseRules(rulesString) {
    const rules = [];
    const statements = this.tokenizeStatements(rulesString);

    for (const statement of statements) {
      const rule = this.parseStatement(statement);
      if (rule) rules.push(rule);
    }

    return rules;
  }

  /**
   * Split rules by semicolon, handling edge cases
   */
  tokenizeStatements(rulesString) {
    // Clean up whitespace and split by semicolon
    const cleaned = rulesString.trim();
    if (!cleaned) {
      throw new Error('Empty rules string provided');
    }

    // Split by semicolon but respect quoted values
    const statements = [];
    let current = '';
    let inQuotes = false;
    let quoteChar = null;

    for (let i = 0; i < cleaned.length; i++) {
      const char = cleaned[i];

      if ((char === '"' || char === "'") && cleaned[i-1] !== '\\') {
        if (!inQuotes) {
          inQuotes = true;
          quoteChar = char;
        } else if (char === quoteChar) {
          inQuotes = false;
          quoteChar = null;
        }
      }

      if (char === ';' && !inQuotes) {
        if (current.trim()) {
          statements.push(current.trim());
        }
        current = '';
      } else {
        current += char;
      }
    }

    // Don't forget the last statement
    if (current.trim()) {
      statements.push(current.trim());
    }

    return statements;
  }

  /**
   * Parse a single statement into selector and actions
   */
  parseStatement(statement) {
    // Find the colon separator
    const colonIndex = statement.indexOf(':');

    if (colonIndex === -1) {
      throw new Error(
        `Invalid statement format: "${statement}"\n` +
        `Expected: "selector: actions"\n` +
        `Example: "self: +active -inactive aria-selected=true"`
      );
    }

    const selector = statement.substring(0, colonIndex).trim();
    const actionsString = statement.substring(colonIndex + 1).trim();

    if (!selector) {
      throw new Error(
        `Empty selector in statement: "${statement}"\n` +
        `Supported selectors: ${Object.keys(this.supportedSelectors).join(', ')}`
      );
    }

    if (!actionsString) {
      throw new Error(
        `No actions specified for selector "${selector}"\n` +
        `Expected actions like: +class, -class, attribute=value`
      );
    }

    const actions = this.parseActions(actionsString);

    return { selector, actions };
  }

  /**
   * Parse action string into structured actions
   */
  parseActions(actionsString) {
    const actions = [];
    const tokens = this.tokenizeActions(actionsString);

    for (const token of tokens) {
      const action = this.parseActionToken(token);
      if (action) actions.push(action);
    }

    return actions;
  }

  /**
   * Tokenize actions, handling multiple classes syntax
   */
  tokenizeActions(actionsString) {
    const tokens = [];
    let current = '';
    let inBrackets = false;

    for (let i = 0; i < actionsString.length; i++) {
      const char = actionsString[i];

      if (char === '[') {
        inBrackets = true;
        current += char;
      } else if (char === ']') {
        inBrackets = false;
        current += char;
      } else if (char === ' ' && !inBrackets) {
        if (current.trim()) {
          tokens.push(current.trim());
        }
        current = '';
      } else {
        current += char;
      }
    }

    if (current.trim()) {
      tokens.push(current.trim());
    }

    return tokens;
  }

  /**
   * Parse individual action token
   */
  parseActionToken(token) {
    // Handle class additions: +class or +[class1,class2]
    if (token.startsWith('+')) {
      const value = token.substring(1);

      if (value.startsWith('[') && value.endsWith(']')) {
        // Multiple classes
        const classList = value.slice(1, -1).split(',').map(c => c.trim());
        return { type: 'addClass', classes: classList };
      } else {
        // Single class
        return { type: 'addClass', classes: [value] };
      }
    }

    // Handle class removals: -class or -[class1,class2]
    if (token.startsWith('-')) {
      const value = token.substring(1);

      if (value.startsWith('[') && value.endsWith(']')) {
        // Multiple classes
        const classList = value.slice(1, -1).split(',').map(c => c.trim());
        return { type: 'removeClass', classes: classList };
      } else {
        // Single class
        return { type: 'removeClass', classes: [value] };
      }
    }

    // Handle attribute assignments: key=value
    if (token.includes('=')) {
      const [key, ...valueParts] = token.split('=');
      const value = valueParts.join('='); // Handle values with = in them

      if (!key.trim()) {
        throw new Error(
          `Invalid attribute assignment: "${token}"\n` +
          `Expected format: attribute=value\n` +
          `Example: aria-selected=true`
        );
      }

      return {
        type: 'setAttribute',
        attribute: key.trim(),
        value: value.trim().replace(/^["']|["']$/g, '') // Remove quotes if present
      };
    }

    throw new Error(
      `Unknown action format: "${token}"\n` +
      `Supported actions:\n` +
      `  +classname    : Add a class\n` +
      `  -classname    : Remove a class\n` +
      `  +[c1,c2]      : Add multiple classes\n` +
      `  -[c1,c2]      : Remove multiple classes\n` +
      `  attribute=val : Set an attribute`
    );
  }

  /**
   * Resolve selector to actual DOM elements
   */
  resolveSelector(selector, clickedElement) {
    // Interpolate variables first
    const interpolated = this.interpolateVariables(selector, clickedElement);

    // Handle special selectors with optional continuation
    if (interpolated === 'self' || interpolated.startsWith('self ') || interpolated.startsWith('self>')) {
      const baseElements = [clickedElement];
      const remainder = interpolated.substring(4).trim();
      if (!remainder) return baseElements;
      return this.queryFromElements(baseElements, remainder);
    }

    if (interpolated === 'siblings' || interpolated.startsWith('siblings ') || interpolated.startsWith('siblings>')) {
      const parent = clickedElement.parentElement;
      if (!parent) return [];
      const baseElements = Array.from(parent.children).filter(el => el !== clickedElement);
      const remainder = interpolated.substring(8).trim();
      if (!remainder) return baseElements;
      return this.queryFromElements(baseElements, remainder);
    }

    if (interpolated === 'parent' || interpolated.startsWith('parent ') || interpolated.startsWith('parent>')) {
      const baseElements = clickedElement.parentElement ? [clickedElement.parentElement] : [];
      const remainder = interpolated.substring(6).trim();
      if (!remainder) return baseElements;
      return this.queryFromElements(baseElements, remainder);
    }

    // Handle CSS combinators
    if (interpolated.startsWith('~')) {
      // General sibling combinator
      const selectorPart = interpolated.substring(1).trim();
      const siblings = [];
      let sibling = clickedElement.nextElementSibling;

      while (sibling) {
        if (!selectorPart || sibling.matches(selectorPart)) {
          siblings.push(sibling);
        }
        sibling = sibling.nextElementSibling;
      }
      return siblings;
    }

    if (interpolated.startsWith('+')) {
      // Adjacent sibling combinator
      const selectorPart = interpolated.substring(1).trim();
      const next = clickedElement.nextElementSibling;

      if (next && (!selectorPart || next.matches(selectorPart))) {
        return [next];
      }
      return [];
    }

    if (interpolated.startsWith('>')) {
      // Child combinator
      const selectorPart = interpolated.substring(1).trim();
      if (!selectorPart) {
        return Array.from(clickedElement.children);
      }
      return Array.from(clickedElement.querySelectorAll(':scope > ' + selectorPart));
    }

    if (interpolated.startsWith('^')) {
      // Traverse up to parent
      const selectorPart = interpolated.substring(1).trim();
      const parent = clickedElement.closest(selectorPart);
      return parent ? [parent] : [];
    }

    // Try to use the selector as a regular CSS selector
    try {
      // Search from document for ID selectors, otherwise from clicked element
      if (interpolated.startsWith('#')) {
        return Array.from(document.querySelectorAll(interpolated));
      }

      // Otherwise, search within the clicked element's context
      return Array.from(clickedElement.querySelectorAll(interpolated));
    } catch (e) {
      throw new Error(
        `Invalid selector: "${selector}"\n` +
        `After interpolation: "${interpolated}"\n` +
        `Supported patterns:\n` +
        `  self              : The clicked element\n` +
        `  siblings          : All siblings\n` +
        `  parent            : Direct parent\n` +
        `  ~ selector        : Following siblings\n` +
        `  + selector        : Next sibling\n` +
        `  > selector        : Direct children\n` +
        `  ^ selector        : Closest parent matching selector\n` +
        `  #id, .class, etc  : Standard CSS selectors`
      );
    }
  }

  /**
   * Query from a set of base elements
   */
  queryFromElements(elements, selectorPart) {
    const results = [];
    for (const element of elements) {
      // Handle child combinator
      if (selectorPart.startsWith('>')) {
        const childSelector = selectorPart.substring(1).trim();
        if (!childSelector) {
          results.push(...Array.from(element.children));
        } else {
          results.push(...Array.from(element.querySelectorAll(':scope > ' + childSelector)));
        }
      }
      // Handle descendant or other selectors
      else if (selectorPart) {
        results.push(...Array.from(element.querySelectorAll(selectorPart)));
      }
    }
    return results;
  }

  /**
   * Interpolate variables in selector
   */
  interpolateVariables(selector, element) {
    return selector.replace(/\{([^}]+)\}/g, (match, varName) => {
      // Handle data attributes
      if (varName.startsWith('data-')) {
        return element.dataset[varName.substring(5)] || '';
      }

      // Handle id
      if (varName === 'id') {
        return element.id || '';
      }

      // Handle other attributes
      if (varName.startsWith('attr:')) {
        const attrName = varName.substring(5);
        return element.getAttribute(attrName) || '';
      }

      // Handle class index
      if (varName.startsWith('class[')) {
        const indexMatch = varName.match(/class\[(\d+)\]/);
        if (indexMatch) {
          const index = parseInt(indexMatch[1]);
          return element.classList[index] || '';
        }
      }

      // Try as a direct attribute
      return element.getAttribute(varName) || '';
    });
  }

  /**
   * Execute parsed rules
   */
  executeRules(rules, clickedElement) {
    if (this.debug) {
      console.group('🎯 RuleApplier Debug');
      console.log(`Clicked element:`, clickedElement);
    }

    for (const rule of rules) {
      const interpolated = this.interpolateVariables(rule.selector, clickedElement);
      const elements = this.resolveSelector(rule.selector, clickedElement);

      if (this.debug) {
        console.group(`📌 Rule: "${rule.selector}"`);
        if (rule.selector !== interpolated) {
          console.log(`  Interpolated to: "${interpolated}"`);
        }
        console.log(`  Found ${elements.length} element(s)`);
        if (elements.length > 0) {
          console.log(`  Elements:`, elements);
          console.log(`  Actions:`, rule.actions.map(a => {
            if (a.type === 'addClass') return `+${a.classes.join(', +')}`;
            if (a.type === 'removeClass') return `-${a.classes.join(', -')}`;
            if (a.type === 'setAttribute') return `${a.attribute}=${a.value}`;
          }).join(' '));
        }
        console.groupEnd();
      }

      if (elements.length === 0) {
        const hasVariables = rule.selector.includes('{');

        console.warn(
          `❌ No elements found for selector!\n\n` +
          `Original selector: "${rule.selector}"\n` +
          (hasVariables ? `Interpolated to:   "${interpolated}"\n\n` : '') +
          `Clicked element: <${clickedElement.tagName.toLowerCase()}${clickedElement.id ? ` id="${clickedElement.id}"` : ''}>\n` +
          (hasVariables ? `\n💡 Check if the interpolated selector matches any element IDs/classes in your HTML.` : ''),
          clickedElement
        );
        continue;
      }

      for (const element of elements) {
        this.applyActions(element, rule.actions);
      }
    }

    if (this.debug) {
      console.groupEnd();
    }
  }

  /**
   * Apply actions to an element
   */
  applyActions(element, actions) {
    for (const action of actions) {
      switch (action.type) {
        case 'addClass':
          element.classList.add(...action.classes);
          break;

        case 'removeClass':
          element.classList.remove(...action.classes);
          break;

        case 'setAttribute':
          if (action.value === 'true') {
            element.setAttribute(action.attribute, 'true');
          } else if (action.value === 'false') {
            element.setAttribute(action.attribute, 'false');
          } else {
            element.setAttribute(action.attribute, action.value);
          }
          break;
      }
    }
  }
}

// Create global instance and helper function
const ruleApplier = new RuleApplier();

function applyRules(rulesString, event, options = {}) {
  // Handle event options
  if (options.preventDefault && event?.preventDefault) {
    event.preventDefault();
  }
  if (options.stopPropagation && event?.stopPropagation) {
    event.stopPropagation();
  }

  // Get the clicked element from event or use currentTarget
  const clickedElement = event?.currentTarget || event?.target || this;

  try {
    ruleApplier.applyRules(rulesString, clickedElement);
  } catch (error) {
    console.error('Rule Application Error:', error);
    // In development, you might want to throw; in production, perhaps just log
    if (window.DEBUG_RULES) {
      throw error;
    }
  }
}

// Export for ES6 modules
export { RuleApplier, applyRules };

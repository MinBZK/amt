/**
 * Declarative Rule Application System
 */

export class RuleApplier {
  constructor();
  applyRules(rulesString: string, clickedElement: HTMLElement): void;
}

export interface ApplyRulesOptions {
  preventDefault?: boolean;
  stopPropagation?: boolean;
}

export function applyRules(
  rulesString: string,
  event: Event,
  options?: ApplyRulesOptions
): void;

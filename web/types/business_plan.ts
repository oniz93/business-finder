export interface BusinessPlan {
  index: Index;
  title: string;
  executive_summary: string;
  problem: string;
  solution: string;
  market_analysis: MarketAnalysis;
  competition: Competition;
  marketing_strategy: MarketingStrategy;
  management_team: ManagementTeam;
  financial_projections: FinancialProjections;
  call_to_action: string;
  summary_text: string;
}

export interface Index {
  _index: string;
  _id: string;
}

export interface MarketAnalysis {
  target_market: string;
  market_size: string;
  trends: string[];
}

export interface Competition {
  competitors: string[];
  competitive_advantages: string[];
}

export interface MarketingStrategy {
  outreach: string[];
  retention: string[];
}

export interface ManagementTeam {
  placeholder: string;
}

export interface FinancialProjections {
  placeholder: string;
}

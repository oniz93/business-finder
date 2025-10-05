export interface BusinessPlan {
  subreddit?: string;
  cluster_id?: number;
  ids_in_cluster?: string[];
  texts?: string[];
  summary?: string;
  total_ups?: number;
  total_downs?: number;
  title?: string;
  executive_summary?: string;
  problem?: string;
  solution?: string;
  market_analysis?: MarketAnalysis;
  competition?: Competition;
  marketing_strategy?: MarketingStrategy;
  management_team?: ManagementTeam;
  financial_projections?: FinancialProjections;
  call_to_action?: string;
}

export interface MarketAnalysis {
  target_market?: string[] | string;
  market_size?: string;
  trends?: string[];
}

export interface Competition {
  competitors?: string[];
  direct_competitors?: string[];
  indirect_competitors?: string[];
  competitive_advantages?: string[];
}

export interface MarketingStrategy {
  approach?: string;
  channels?: string[];
  content_strategy?: string;
  community_building?: string[];
  customer_acquisition?: string[];
  digital_marketing?: string[];
  distribution_channels?: string;
  influencer_marketing?: string[];
  messaging?: string;
  online_presence?: string;
  outreach?: string[] | string;
  outreach_channels?: string[];
  outreach_methods?: string[];
  partnerships?: string[];
  paid_advertising?: string;
  pricing_strategy?: string;
  public_relations?: string[];
  reach_target_market?: string[];
  retention?: string[];
  seo_optimization?: string;
  value_proposition?: string;
}

export interface Role {
    role: string;
    description: string;
}

export interface ManagementTeam {
  placeholder?: string;
  description?: string;
  roles?: Role[];
}

export interface FinancialProjections {
  placeholder?: string;
  description?: string;
  revenue_streams?: string[];
  cost_structure?: string[];
}

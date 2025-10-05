import React from 'react';
import { ScrollView, View, Text, StyleSheet } from 'react-native';
import { BusinessPlan } from '../types/business_plan';
import Markdown from 'react-native-markdown-display';

interface Props {
  plan: BusinessPlan;
}

const formatTitle = (title: string) => {
  return title
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

const BusinessPlanCard: React.FC<Props> = ({ plan }) => {

  const renderValue = (value: any, level = 0): React.ReactNode => {
    if (!value) {
      return null;
    }
    if (typeof value === 'string') {
      return <Markdown style={{ body: styles.text }}>{value}</Markdown>;
    }
    if (Array.isArray(value)) {
      return (
        <View>
          {value.map((item, index) => {
            if (typeof item === 'object' && item !== null) {
              return (
                <View key={index} style={styles.nestedObject}>
                  {Object.entries(item).map(([k, v]) => (
                    <View key={k}>
                      <Text style={styles.h4}>{formatTitle(k)}</Text>
                      {renderValue(v, level + 1)}
                    </View>
                  ))}
                </View>
              );
            }
            return <Markdown key={index} style={{ body: styles.listItem }}>{`- ${item}`}</Markdown>;
          })}
        </View>
      );
    }
    if (typeof value === 'object') {
      return (
        <View style={{ marginLeft: level * 10 }}>
          {Object.entries(value).map(([key, val]) => {
            if (!val) return null;
            return (
              <View key={key}>
                <Text style={styles.h3}>{formatTitle(key)}</Text>
                {renderValue(val, level + 1)}
              </View>
            );
          })}
        </View>
      );
    }
    return null;
  };

  const renderSection = (key: string, value: any) => {
    if (!value) {
      return null;
    }
    if (key === 'title') {
      return <Text key={key} style={styles.title}>{value}</Text>;
    }
    if (['subreddit', 'cluster_id', 'ids_in_cluster', 'texts', 'total_ups', 'total_downs', 'summary'].includes(key)) {
      return null;
    }

    return (
      <View key={key}>
        <Text style={styles.h2}>{formatTitle(key)}</Text>
        {renderValue(value)}
      </View>
    );
  };

  if (!plan) {
    return null;
  }

  const orderedPlan = {
    title: plan.title,
    executive_summary: plan.executive_summary,
    problem: plan.problem,
    solution: plan.solution,
    market_analysis: plan.market_analysis,
    competition: plan.competition,
    marketing_strategy: plan.marketing_strategy,
    management_team: plan.management_team,
    financial_projections: plan.financial_projections,
    call_to_action: plan.call_to_action,
    ...plan
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.card}>
        {Object.entries(orderedPlan).map(([key, value]) => renderSection(key, value))}
      </View>
      {(plan.summary || (plan.texts && plan.texts.length > 0)) && (
        <View style={styles.sourceCard}>
            <Text style={styles.h2}>Source Data</Text>
            {plan.summary && (
                <View>
                    <Text style={styles.h3}>Summary</Text>
                    <Markdown style={{ body: styles.text }}>{plan.summary}</Markdown>
                </View>
            )}
            {plan.texts && plan.texts.length > 0 && (
                <View>
                    <Text style={styles.h3}>Original Texts</Text>
                    {plan.texts.map((text, index) => (
                        <Markdown key={index} style={{ body: styles.sourceText }}>{text.replace(/\n\n---\n\n/g, '\n\n---\n\n')}</Markdown>
                    ))}
                </View>
            )}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#191970',
  },
  card: {
    backgroundColor: '#2c3e50',
    borderRadius: 8,
    padding: 20,
    margin: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#D3D3D3',
  },
  h2: {
    fontSize: 22,
    fontWeight: 'bold',
    marginTop: 15,
    marginBottom: 5,
    color: '#D3D3D3',
  },
  h3: {
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 10,
    marginBottom: 5,
    color: '#D3D3D3',
  },
  h4: {
    fontSize: 16,
    fontWeight: 'bold',
    marginTop: 10,
    marginBottom: 5,
    color: '#D3D3D3',
  },
  text: {
    fontSize: 14,
    lineHeight: 20,
    color: '#D3D3D3',
  },
  listItem: {
    fontSize: 14,
    lineHeight: 20,
    marginLeft: 10,
    color: '#D3D3D3',
  },
  nestedObject: {
    marginLeft: 10,
    borderLeftWidth: 2,
    borderLeftColor: '#445c75',
    paddingLeft: 10,
    marginTop: 5,
    marginBottom: 5,
  },
  codeBlock: {
    backgroundColor: '#000000',
    padding: 10,
    borderRadius: 4,
  },
  sourceCard: {
    backgroundColor: '#2c3e50',
    borderRadius: 8,
    padding: 20,
    margin: 20,
    marginTop: 0,
  },
  sourceText: {
    fontSize: 12,
    lineHeight: 18,
    color: '#B0C4DE',
    fontStyle: 'italic',
    borderLeftWidth: 2,
    borderLeftColor: '#445c75',
    paddingLeft: 10,
    marginTop: 10,
  },
});

export default BusinessPlanCard;

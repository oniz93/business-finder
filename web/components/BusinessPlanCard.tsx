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
  const renderSection = (key: string, value: any) => {
    if (key === 'title') {
      return <Text key={key} style={styles.title}>{value}</Text>;
    }

    if (typeof value === 'string') {
      return (
        <View key={key}>
          <Text style={styles.h2}>{formatTitle(key)}</Text>
          <Markdown style={{body: styles.text}}>{value}</Markdown>
        </View>
      );
    } else if (Array.isArray(value)) {
      return (
        <View key={key}>
          <Text style={styles.h2}>{formatTitle(key)}</Text>
          {value.map((item, index) => (
            <Markdown key={index} style={{body: styles.listItem}}> - {item}</Markdown>
          ))}
        </View>
      );
    } else if (typeof value === 'object' && value !== null) {
      return (
        <View key={key}>
          <Text style={styles.h2}>{formatTitle(key)}</Text>
          <Markdown style={{body: styles.text, code_block: styles.codeBlock}}>
            {'```json\n' + JSON.stringify(value, null, 2) + '\n```'}
          </Markdown>
        </View>
      );
    }
    return null;
  };

  if (!plan) {
    return null;
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.card}>
        {Object.entries(plan).map(([key, value]) => {
          if (key === 'index') return null; // Don't render the index
          return renderSection(key, value);
        })}
      </View>
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
  codeBlock: {
    backgroundColor: '#000000',
    padding: 10,
    borderRadius: 4,
  },
});

export default BusinessPlanCard;

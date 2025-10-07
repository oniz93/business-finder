import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator, Text, TouchableOpacity, SafeAreaView, StyleSheet } from 'react-native';
import { getRandomPlan } from '../../services/api';
import { BusinessPlan } from '../../types/business_plan';
import BusinessPlanCard from '../../components/BusinessPlanCard';
import { LinearGradient } from 'expo-linear-gradient';
import { Link } from 'expo-router';

const FeedScreen = () => {
  const [plan, setPlan] = useState<BusinessPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRandomPlan = async () => {
    setLoading(true);
    setError(null);
    try {
      const randomPlan = await getRandomPlan();
      if (randomPlan) {
        setPlan(randomPlan);
      } else {
        setError('Failed to fetch business plan. Please try again.');
      }
    } catch (error) {
      setError('Failed to fetch business plan. Please try again.');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRandomPlan();
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient
        colors={['#1a202c', '#12161f', '#0d1117']}
        style={styles.gradient}
      />
      <View style={styles.topBar}>
        <TouchableOpacity style={styles.nextButton} onPress={loadRandomPlan}>
          <Text style={styles.nextButtonText}>Next Idea</Text>
        </TouchableOpacity>
      </View>
      {loading && (
        <View style={styles.centeredContainer}>
          <ActivityIndicator size="large" color="#ffffff" />
        </View>
      )}
      {error && (
        <View style={styles.centeredContainer}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadRandomPlan}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}
      {plan && !loading && !error && (
        <View style={styles.contentContainer}>
          <BusinessPlanCard plan={plan} />
          <Link href={`/plan/${plan.id}`} asChild>
            <TouchableOpacity style={styles.viewPlanButton}>
              <Text style={styles.viewPlanButtonText}>View Full Business Plan</Text>
            </TouchableOpacity>
          </Link>
        </View>
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    height: '100%',
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'center',
    padding: 16,
    alignItems: 'center',
  },
  nextButton: {
    backgroundColor: '#2563eb',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  nextButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  centeredContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    color: '#cbd5e0',
    fontSize: 16,
    marginBottom: 20,
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  retryButton: {
    backgroundColor: '#ffffff',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#1a202c',
    fontSize: 16,
    fontWeight: 'bold',
  },
  contentContainer: {
    flex: 1,
    justifyContent: 'center',
    padding: 16,
  },
  viewPlanButton: {
    backgroundColor: '#10b981',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignSelf: 'center',
    marginTop: 24,
  },
  viewPlanButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default FeedScreen;
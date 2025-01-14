import os
import makeit.global_config as gc
from pymongo import MongoClient
from makeit.utilities.io.logger import MyLogger
from makeit.utilities.buyable.pricer import Pricer
from makeit.synthetic.context.nearestneighbor import NNContextRecommender
from makeit.synthetic.context.neuralnetwork import NeuralNetContextRecommender
from makeit.synthetic.enumeration.transformer import ForwardTransformer
from makeit.retrosynthetic.transformer import RetroTransformer
from makeit.synthetic.evaluation.template_based import TemplateNeuralNetScorer
from makeit.synthetic.evaluation.template_free import TemplateFreeNeuralNetScorer
from makeit.synthetic.evaluation.fast_filter import FastFilterScorer
import sys
model_loader_loc = 'model_loader'


def load_Retro_Transformer(mincount=25, mincount_chiral=10, chiral=True):
    '''    
    Load the model and databases required for the retro transformer. Returns the retro transformer, ready to run.
    '''
    MyLogger.print_and_log(
        'Loading retro synthetic template database...', model_loader_loc)
    retroTransformer = RetroTransformer(mincount=mincount, mincount_chiral=mincount_chiral)
    retroTransformer.load(chiral=chiral)
    MyLogger.print_and_log(
        'Retro synthetic transformer loaded.', model_loader_loc)
    return retroTransformer


def load_Databases(worker_no = 0):
    '''
    Load the different databases that will be used: Reactions, Instances, Chemicals, Buyables, Solvents, Retro templates and Synthetic templates
    '''

    db_client = MongoClient(gc.MONGO['path'], gc.MONGO[
                            'id'], connect=gc.MONGO['connect'])
    if worker_no == 0:
        MyLogger.print_and_log('Loading databases...', model_loader_loc)
    db = db_client[gc.REACTIONS['database']]
    REACTION_DB = db[gc.REACTIONS['collection']]

    db = db_client[gc.INSTANCES['database']]
    INSTANCE_DB = db[gc.INSTANCES['collection']]
    db = db_client[gc.CHEMICALS['database']]
    CHEMICAL_DB = db[gc.CHEMICALS['collection']]

    db = db_client[gc.BUYABLES['database']]
    BUYABLE_DB = db[gc.BUYABLES['collection']]
    db = db_client[gc.SOLVENTS['database']]
    SOLVENT_DB = db[gc.SOLVENTS['collection']]

    db = db_client[gc.RETRO_TRANSFORMS['database']]
    RETRO_DB = db[gc.RETRO_TRANSFORMS['collection']]
    RETRO_DB_CHIRAL = db[gc.RETRO_TRANSFORMS_CHIRAL['collection']]
    db = db_client[gc.SYNTH_TRANSFORMS['database']]
    SYNTH_DB = db[gc.SYNTH_TRANSFORMS['collection']]

    databases = {
        'Reaction_Database': REACTION_DB,
        'Instance_Database': INSTANCE_DB,
        'Chemical_Database': CHEMICAL_DB,
        'Buyable_Database': BUYABLE_DB,
        'Solvent_Database': SOLVENT_DB,
        'Retro_Database': RETRO_DB,
        'Retro_Database_Chiral': RETRO_DB_CHIRAL,
        'Synth_Database': SYNTH_DB
    }
    if worker_no == 0:
        MyLogger.print_and_log('Databases loaded.', model_loader_loc)
    return databases


def load_Pricer(chemical_database, buyable_database):
    '''
    Load a pricer using the chemicals database and database of buyable chemicals
    '''
    MyLogger.print_and_log('Loading pricing model...', model_loader_loc)
    pricerModel = Pricer()
    pricerModel.load(chemical_database, buyable_database)
    MyLogger.print_and_log('Pricer Loaded.', model_loader_loc)
    return pricerModel


def load_Forward_Transformer(mincount=100, worker_no = 0):
    '''
    Load the forward prediction neural network
    '''
    if worker_no==0:
        MyLogger.print_and_log('Loading forward prediction model...', model_loader_loc)
        
    transformer = ForwardTransformer(mincount=mincount)
    transformer.load(worker_no = worker_no)
    if worker_no==0:
        MyLogger.print_and_log('Forward transformer loaded.', model_loader_loc)
    return transformer


def load_fastfilter():
    ff = FastFilterScorer()
    ff.load(model_path =gc.FAST_FILTER_MODEL['trained_model_path'])
    return ff


def load_templatebased(mincount=25, celery=False, worker_no = 0):
    transformer = None
    databases = load_Databases(worker_no = worker_no)
    if not celery:
        transformer = load_Forward_Transformer(mincount=mincount, worker_no = worker_no)

    scorer = TemplateNeuralNetScorer(
        forward_transformer=transformer, celery=celery)
    scorer.load(gc.PREDICTOR['trained_model_path'], worker_no = worker_no)
    return scorer


def load_templatefree():
    # Still has to be implemented
    return TemplateFreeNeuralNetScorer()


def load_Context_Recommender(context_recommender, max_contexts=10):
    '''
    Load the context recommendation model
    '''
    MyLogger.print_and_log('Loading context recommendation model: {}...'.format(
        context_recommender), model_loader_loc)
    if context_recommender == gc.nearest_neighbor:
        recommender = NNContextRecommender(max_contexts=max_contexts)
        recommender.load(model_path=gc.CONTEXT_REC[
                         'model_path'], info_path=gc.CONTEXT_REC['info_path'])
    elif context_recommender == gc.neural_network:
        recommender = NeuralNetContextRecommender(max_contexts=max_contexts)
        recommender.load(model_path=gc.NEURALNET_CONTEXT_REC['model_path'], info_path=gc.NEURALNET_CONTEXT_REC[
                       'info_path'], weights_path=gc.NEURALNET_CONTEXT_REC['weights_path'])
    else:
        raise NotImplementedError
    MyLogger.print_and_log('Context recommender loaded.', model_loader_loc)
    return recommender

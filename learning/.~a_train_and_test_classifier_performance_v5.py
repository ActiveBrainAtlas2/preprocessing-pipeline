import sys
import os
import time

import numpy as np
try:
    import mxnet as mx
except:
    sys.stderr.write("Cannot import mxnet.\n")
#import matplotlib.pyplot as plt
from skimage.exposure import rescale_intensity
from skimage.transform import rotate

sys.path.append(os.environ['REPO_DIR'] + '/utilities')
from utilities2015 import *
from metadata import *
from data_manager import *
from learning_utilities import *
from distributed_utilities import *
from visualization_utilities import *



from sklearn.externals import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC, SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier

sys.path.append('/home/yuncong/csd395/xgboost/python-package')
try:
    from xgboost.sklearn import XGBClassifier
except:
    sys.stderr.write('xgboost is not loaded.')


win_id = 7
train_stacks = ['MD589']
test_stacks = ['MD589']
stack_stain = {'MD589': 'N'}



batch_size = 256
model_dir_name = 'inception-bn-blue'
model_name = 'inception-bn-blue'
model, mean_img = load_mxnet_model(model_dir_name=model_dir_name, model_name=model_name,
                                   num_gpus=1, batch_size=batch_size)


# Number of sections on which to sample examples from.
stack_section_number = defaultdict(dict)

for name_u in all_known_structures:
    for st in train_stacks:
        stack_section_number[st][name_u] = 10
#         if name_u == '4N' or name_u == '10N':
#             stack_section_number[st][name_u] = 20
#         else:
#             stack_section_number[st][name_u] = 10
    for st in test_stacks:
        stack_section_number[st][name_u] = 10
stack_section_number.default_factory = None


grid_indices_lookup_allStacks = {}
# Saves pandas lookup table of all patches for all structures
for stack in set(train_stacks + test_stacks):
    grid_indices_lookup_allStacks[stack] = \
    DataManager.load_annotation_to_grid_indices_lookup(stack=stack, win_id=win_id,
                                                       by_human=True, timestamp='latest',
                                                      return_locations=True)
# Extracts a list of the columns. ex: '12N', '12N_negative', '12N_surround_200um_10N'
from itertools import chain
all_labels = sorted(list(set(chain.from_iterable(set(grid_indices_lookup_allStacks[st].columns.tolist())
                                                 for st in train_stacks + test_stacks))))



# train_scheme = 'stretch_min_max'
# train_scheme = 'normalize_mu_sigma_global_(-1,5)'
# train_scheme = 'normalize_mu_region_sigma_wholeImage_(-1,5)'
# train_scheme = 'normalize_mu_region_sigma_wholeImage_(-1,9)'
train_scheme = 'none'

# test_scheme = 'stretch_min_max'
# test_scheme = 'normalize_mu_sigma_global_(-1,5)'
# test_scheme = 'normalize_mu_region_sigma_wholeImage_(-1,5)'
# test_scheme = 'normalize_mu_region_sigma_wholeImage_(-1,9)'
test_scheme = 'none'


existing_classifier_id = None
# existing_classifier_id = 998 # If set, not train from scratch
extract_train_features = True

method = 'cnn'

prep_id = 'alignedBrainstemCrop'




for stack in test_stacks:

    target_locations = grid_parameters_to_sample_locations(grid_spec=win_id_to_gridspec(win_id=7, stack=stack))
    source_locations = grid_parameters_to_sample_locations(grid_spec=win_id_to_gridspec(win_id=8, stack=stack))
    target_locations_mapped_to_source_locations, target_indices_to_source_indices_mapping = align_grid_specs(source_locations=source_locations, target_locations=target_locations, stack=stack)

    target_locations_to_source_locations_mapping = {tuple(tgt_loc): tuple(src_loc)
                        for tgt_loc, src_loc in zip(target_locations, target_locations_mapped_to_source_locations)}

    for sec in metadata_cache['valid_sections'][stack]:

        print stack, sec

        features_100um, locations_100um = DataManager.load_dnn_features_v2(stack=stack, sec=sec,
                                                                           prep_id=prep_id, win_id=7,
                                                                           normalization_scheme='none',
                                                                           model_name=model_name)

        features_200um, locations_200um = DataManager.load_dnn_features_v2(stack=stack, sec=sec,
                                                               prep_id=prep_id, win_id=8,
                                                               normalization_scheme='none',
                                                               model_name=model_name)

        locations_200um_to_indices_200um_in_loaded_pool_mapping = {tuple(loc_200um): idx_200um_in_loaded_pool
                                for idx_200um_in_loaded_pool, loc_200um in enumerate(locations_200um)}

        features = []
        locations = []
        for idx_100um_in_loaded_pool, loc_100um in enumerate(locations_100um):
            loc_200um = target_locations_to_source_locations_mapping[tuple(loc_100um)]
            if tuple(loc_200um) in locations_200um_to_indices_200um_in_loaded_pool_mapping:
                # check if the 100um grid mapped to a 200um grid that has features associated
                idx_200um_in_loaded_pool = locations_200um_to_indices_200um_in_loaded_pool_mapping[tuple(loc_200um)]

                f = np.concatenate([features_100um[idx_100um_in_loaded_pool],
                                   features_200um[idx_200um_in_loaded_pool]], axis=-1)
                features.append(f)
                locations.append(locations_100um[idx_100um_in_loaded_pool])

        DataManager.save_dnn_features_v2(features=features, locations=locations,
                         stack=stack, sec=sec, prep_id=prep_id,
                         win_id=7, normalization_scheme='none',
                         model_name='concat_100um_200um')


for stack in train_stacks:

    size100um_locations = grid_parameters_to_sample_locations(grid_spec=win_id_to_gridspec(win_id=7, stack=stack))
    size200um_locations = grid_parameters_to_sample_locations(grid_spec=win_id_to_gridspec(win_id=8, stack=stack))
    size50um_locations = grid_parameters_to_sample_locations(grid_spec=win_id_to_gridspec(win_id=11, stack=stack))

    size100um_locations_mapped_to_size200um_locations, \
    size100um_indices_to_size200um_indices_mapping = \
    align_grid_specs(source_locations=size200um_locations,
                     target_locations=size100um_locations,
                     stack=stack)

    size100um_locations_to_size200um_locations_mapping = {tuple(tgt_loc): tuple(src_loc)
                        for tgt_loc, src_loc in zip(size100um_locations,
                                                    size100um_locations_mapped_to_size200um_locations)}

    size100um_locations_mapped_to_size50um_locations, \
    size100um_indices_to_size50um_indices_mapping = \
    align_grid_specs(source_locations=size50um_locations,
                     target_locations=size100um_locations,
                     stack=stack)
    size100um_locations_to_size50um_locations_mapping = {tuple(tgt_loc): tuple(src_loc)
                        for tgt_loc, src_loc in zip(size100um_locations,
                                                    size100um_locations_mapped_to_size50um_locations)}

    for sec in metadata_cache['valid_sections'][stack]:

        print stack, sec

        features_100um, locations_100um = DataManager.load_dnn_features_v2(stack=stack, sec=sec,
                                                                           prep_id=prep_id, win_id=7,
                                                                           normalization_scheme='none',
                                                                           model_name=model_name)

        features_200um, locations_200um = DataManager.load_dnn_features_v2(stack=stack, sec=sec,
                                                               prep_id=prep_id, win_id=8,
                                                               normalization_scheme='none',
                                                               model_name=model_name)

        features_50um, locations_50um = DataManager.load_dnn_features_v2(stack=stack, sec=sec,
                                                               prep_id=prep_id, win_id=11,
                                                               normalization_scheme='none',
                                                               model_name=model_name)

        locations_200um_to_indices_200um_in_loaded_pool_mapping = {tuple(loc_200um): idx_200um_in_loaded_pool
                                for idx_200um_in_loaded_pool, loc_200um in enumerate(locations_200um)}

        locations_50um_to_indices_50um_in_loaded_pool_mapping = {tuple(loc_50um): idx_50um_in_loaded_pool
                        for idx_50um_in_loaded_pool, loc_50um in enumerate(locations_50um)}


        features = []
        locations = []
        for idx_100um_in_loaded_pool, loc_100um in enumerate(locations_100um):
            loc_200um = size100um_locations_to_size200um_locations_mapping[tuple(loc_100um)]
            loc_50um = size100um_locations_to_size50um_locations_mapping[tuple(loc_100um)]

            if tuple(loc_200um) in locations_200um_to_indices_200um_in_loaded_pool_mapping and \
            tuple(loc_50um) in locations_50um_to_indices_50um_in_loaded_pool_mapping:

                # check if the 100um grid mapped to a 200um grid that has features associated
                idx_200um_in_loaded_pool = locations_200um_to_indices_200um_in_loaded_pool_mapping[tuple(loc_200um)]

                idx_50um_in_loaded_pool = locations_50um_to_indices_50um_in_loaded_pool_mapping[tuple(loc_50um)]

                f = np.concatenate([features_100um[idx_100um_in_loaded_pool],
                                   features_200um[idx_200um_in_loaded_pool],
                                   features_50um[idx_50um_in_loaded_pool]], axis=-1)
                features.append(f)
                locations.append(locations_100um[idx_100um_in_loaded_pool])

        DataManager.save_dnn_features_v2(features=features, locations=locations,
                         stack=stack, sec=sec, prep_id=prep_id,
                         win_id=7, normalization_scheme='none',
                         model_name='concat_100um_200um_50um')


compute_new_addresses = False
# model_name = 'concat_100um_200um'
model_name = 'concat_100um_200um_50um'



for structure in all_known_structures:
# for structure in ['3N']:

    # features_dict = {(scheme, tfv): {} for scheme in schemes for tfv in transforms}
    features_dict = defaultdict(dict)

    ############## Sample and Load training feature vectors #########################################

    if extract_train_features:

        positive_addresses_traindata, negative_addresses_traindata = \
        sample_addresses(train_stacks, structure)

        print '# positive train =', len(positive_addresses_traindata)
        print '# negative train =', len(negative_addresses_traindata)

        addresses_to_compute = positive_addresses_traindata + negative_addresses_traindata

        for variant in [0]:
            features_loaded = read_features(addresses=addresses_to_compute,
                                            scheme=train_scheme, win_id=win_id, prep_id=prep_id,
                                            model=model, mean_img=mean_img, model_name=model_name,
                                            batch_size=batch_size,
                                           method=method,
                                           compute_new_addresses=compute_new_addresses
                                           )

            for addr, f in izip(addresses_to_compute, features_loaded):
                if f is not None:
                    features_dict[(train_scheme, variant)][addr] = f

            del features_loaded

    ############## Sample and Load test feature vectors #############################################

    positive_addresses_testdata, negative_addresses_testdata = \
    sample_addresses(test_stacks, structure)

    print '# positive test =', len(positive_addresses_testdata)
    print '# negative test =', len(negative_addresses_testdata)

    addresses_to_compute = positive_addresses_testdata + negative_addresses_testdata

    for variant in [0]:
        features_loaded = read_features(addresses=addresses_to_compute,
                                        scheme=test_scheme, win_id=win_id, prep_id=prep_id,
                                        model=model, mean_img=mean_img, model_name=model_name,
                                        batch_size=batch_size,
                                           method=method,
                                       compute_new_addresses=compute_new_addresses
                                       )

        for addr, f in izip(addresses_to_compute, features_loaded):
            if f is not None:
                features_dict[(test_scheme, variant)][addr] = f

        del features_loaded

    ########################################################################################

    # n_train_list = [10, 100, 200, 500, 1000, 2000, 5000, 10000, 15000]
#     n_train_list = [10, 1000]
    n_train_list = [1000, 5000, 15000]
#     n_train_list = [1000, 5000]
#     n_train_list = [15000]
    test_metrics_all_ntrain = defaultdict(lambda: defaultdict(list))
    train_metrics_all_ntrain = defaultdict(lambda: defaultdict(list))

    for n_train in n_train_list:

        print "n_train", n_train

        for trial in range(3):
            print "Trial", trial

            ##### Sample from training pool the required number of examples ######

            # If train and test data are from different sets
            n_train_pos = min(n_train, len(positive_addresses_traindata))
#             if len(positive_addresses_traindata) < n_train_pos:
#                 continue
            training_pos_indices = np.random.choice(range(len(positive_addresses_traindata)), n_train_pos, replace=False)

            n_test_pos = min(len(positive_addresses_testdata), 1000)
            test_pos_indices = np.random.choice(range(len(positive_addresses_testdata)), n_test_pos, replace=False)

            # If train and test are from same set
        #     n_pos_total = len(positive_addresses)
        #     n_train_pos = 1000
        #     training_pos_indices = np.random.choice(range(n_pos_total), n_train_pos, replace=False)
        #     test_pos_indices = np.random.choice(np.setdiff1d(range(n_pos_total), training_pos_indices),
        #                                         size=min(2000, n_pos_total-n_train_pos), replace=False)
        #     n_test_pos = len(test_pos_indices)

            # If train and test data are from different sets
            n_train_neg = n_train_pos
            training_neg_indices = np.random.choice(range(len(negative_addresses_traindata)), n_train_neg, replace=False)

            n_test_neg = min(len(negative_addresses_testdata), 1000)
            test_neg_indices = np.random.choice(range(len(negative_addresses_testdata)), n_test_neg, replace=False)

            # If train and test are from same set
        #     n_neg_total = len(negative_addresses)
        #     n_train_neg = 1000
        #     training_neg_indices = np.random.choice(range(n_neg_total), n_train_neg, replace=False)
        #     test_neg_indices = np.random.choice(np.setdiff1d(range(n_neg_total), training_neg_indices),
        #                                         size=min(2000, n_pos_total-n_train_pos), replace=False)
        #     n_test_neg = len(test_neg_indices)

            print "Training: %d positive, %d negative" % (n_train_pos, n_train_neg)
            print "Test: %d positive, %d negative" % (n_test_pos, n_test_neg)

            ################

            if extract_train_features:
                # If train and test data are from different sets
                addresses_train_pos = [positive_addresses_traindata[i] for i in training_pos_indices]
                addresses_train_neg = [negative_addresses_traindata[i] for i in training_neg_indices]

            addresses_test_pos = [positive_addresses_testdata[i] for i in test_pos_indices]
            addresses_test_neg = [negative_addresses_testdata[i] for i in test_neg_indices]

            #################

#             for augment_training in [True, False]:
            for augment_training in [False]:

                feature_classifier_alg = 'lr'
#                 feature_classifier_alg = 'xgb2'
        #             feature_classifier_alg = 'lin_svc'
        #             feature_classifier_alg = 'lin_svc_calib'
                sample_weights = None

                if extract_train_features:

                    if augment_training:
                        train_transforms = range(8)
                    else:
                        train_transforms = range(1)
                    features_train_pos = {(train_scheme, tf_variant):
                                          [features_dict[(train_scheme, tf_variant)][addr]
                                           for addr in addresses_train_pos
                                           if addr in features_dict[(train_scheme, tf_variant)]]
                                              for tf_variant in train_transforms}
                    features_train_neg = {(train_scheme, tf_variant):
                                          [features_dict[(train_scheme, tf_variant)][addr]
                                           for addr in addresses_train_neg
                                           if addr in features_dict[(train_scheme, tf_variant)]]
                                              for tf_variant in train_transforms}

                    train_data = np.concatenate([np.r_[features_train_pos[(train_scheme,tf)],
                                                       features_train_neg[(train_scheme,tf)]]
                                                    for tf in train_transforms])
                    train_labels = np.concatenate([np.r_[np.ones((len(features_train_pos[(train_scheme,tf)]), )),
                                                        -np.ones((len(features_train_neg[(train_scheme,tf)]), ))]
                                                  for tf in train_transforms])

                if existing_classifier_id is None:
                    clf = train_binary_classifier(train_data, train_labels,
                                       alg=feature_classifier_alg,
                                       sample_weights=sample_weights)

    #                 del train_data, features_train_pos, features_train_neg

                    clf_fp = DataManager.get_classifier_filepath(classifier_id=classifier_id, structure=structure)
                    save_data(clf, clf_fp)
#                     upload_to_s3(clf_fp)
                else:
                    sys.stderr.write('Load existing classifiers %d\n' % existing_classifier_id)
                    clf = DataManager.load_classifiers(classifier_id=existing_classifier_id)[structure]

                ######################### Compute train metrics #########################

                if extract_train_features:
                    train_metrics = compute_classification_metrics(clf.predict_proba(train_data)[:,1], train_labels)
                    train_metrics_all_ntrain[n_train][(train_scheme, 'augment' if augment_training else 'no-augment')].append(train_metrics)

                ######################### Test ###############################

                test_transforms = range(1)
                features_test_pos = {(test_scheme, tf_variant):
                                      [features_dict[(test_scheme, tf_variant)][addr]
                                       for addr in addresses_test_pos
                                      if addr in features_dict[(test_scheme, tf_variant)]]
                                          for tf_variant in test_transforms}
                features_test_neg = {(test_scheme, tf_variant):
                                      [features_dict[(test_scheme, tf_variant)][addr]
                                       for addr in addresses_test_neg
                                      if addr in features_dict[(test_scheme, tf_variant)]]
                                          for tf_variant in test_transforms}

                test_data = np.concatenate([np.r_[features_test_pos[(test_scheme,tf_variant)],
                                  features_test_neg[(test_scheme,tf_variant)]]
                                            for tf_variant in train_transforms])
                test_labels = np.concatenate([np.r_[np.ones((len(features_test_pos[(test_scheme,tf_variant)]), )),
                                     -np.ones((len(features_test_neg[(test_scheme,tf_variant)]), ))]
                                            for tf_variant in train_transforms])
                test_metrics = compute_classification_metrics(clf.predict_proba(test_data)[:,1], test_labels)
    #             print "acc@0.5 = %.3f, acc@opt = %.3f, opt_thresh = %.3f, auroc = %.3f, auprc = %.3f" % \
    #             (test_metrics['acc'][0.5], test_metrics['acc'][test_metrics['opt_thresh']], test_metrics['opt_thresh'], test_metrics['auroc'], test_metrics['auprc'])

                test_metrics_all_ntrain[n_train][(test_scheme, 'augment' if augment_training else 'no-augment')].append(test_metrics)

    train_metrics_all_ntrain.default_factory = None
    test_metrics_all_ntrain.default_factory = None

    plot_result_wrt_ntrain(extract_one_metric(test_metrics_all_ntrain, 'acc', 0.5), ylabel='Test accuracy@0.5 threshold');
    plot_result_wrt_ntrain(extract_one_metric(test_metrics_all_ntrain, 'auroc'), ylabel='Area under ROC');

    plot_roc_curve(test_metrics_all_ntrain[1000][(test_scheme,
                  'no-augment')][0]['fp'],
                   test_metrics_all_ntrain[1000][(test_scheme,
                  'no-augment')][0]['tp'],
                  test_metrics_all_ntrain[1000][(test_scheme,
                  'no-augment')][0]['opt_thresh']);

    import uuid

    result = {
        'n_sections': stack_section_number,
        'stain': stack_stain,
        'train_stacks': train_stacks,
        'test_stacks': test_stacks,
        'test_scheme': test_scheme,
        'train_scheme': train_scheme,
        'train_metrics_all_ntrain': train_metrics_all_ntrain,
        'test_metrics_all_ntrain': test_metrics_all_ntrain,
        'structure': structure,
        'method': method,
        'classifier_id': existing_classifier_id if existing_classifier_id is not None else classifier_id
    }

    create_if_not_exists(ROOT_DIR + '/assessment_results_v4/')
    save_pickle(result, ROOT_DIR + '/assessment_results_v4/assessment_result_%s.pkl' % str(uuid.uuid1()).split('-')[0])



np.mean(extract_one_metric(test_metrics_all_ntrain, 'auroc')[15000][('none','no-augment')])

plot_result_wrt_ntrain(extract_one_metric(test_metrics_all_ntrain, 'acc', 0.5), ylabel='Test accuracy@0.5 threshold');
plot_result_wrt_ntrain(extract_one_metric(test_metrics_all_ntrain, 'auroc'), ylabel='Area under ROC');

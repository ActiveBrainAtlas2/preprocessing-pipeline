__author__ = 'Zhongkai_Wu'
__email__ = "zhw272@ucsd.edu"
from posixpath import split
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from toolbox.IOs.save_figures_to_pdf import save_figures_to_pdf

class ComBoxPlot:
    """ [This class generate com offset boxplots in three ways:
            1. comparing com offset of elements between two lists of com dictionaries
            2. comparing com offset of elements of one list to a reference com dictionary
            3. visualize a set of precomputed com offsets
        For each of the above there is a function to plot them immediately, and one that returns the figure object without plotting (ideal for creating pdfs)]
    """
    def __init__(self,prep_list_function = None,landmark_list_function = None):
        """__init__ [creates the ComBoxPlot object]

        :param prep_list_function: [A function that returns a list of brain ids in com lists or corresponding to the offsets], defaults to None
        :param landmark_list_function: [A function that returns a list of shared structures given a list of brain ids use one of the functions in
        IOs/get_landmark_lists.py], defaults to None
        """
        self.prep_list_function = prep_list_function
        self.landmark_list_function = landmark_list_function
        self.figs = []
        self.column_types = ['dx','dy','dz','dist']
        self.postfix = ''
        self.custome_order = None
        self.split = 1
        self.color_list = None

    def get_fig_two_com_dict_list_against_reference(self,comlists,reference,title):
        prep1,prep2,prep3 = comlists.keys()
        comlist1,comlist2,comlist3 = comlists.values()
        self.postfix = prep1
        offset_table1 = self._get_offset_table_from_coms_to_a_reference(comlist1,reference)
        self.postfix = prep2
        offset_table2 = self._get_offset_table_from_coms_to_a_reference(comlist2,reference)
        self.postfix = prep3
        offset_table3 = self._get_offset_table_from_coms_to_a_reference(comlist3,reference)
        offset_table = offset_table1.append(offset_table2,ignore_index = True)
        offset_table = offset_table.append(offset_table3,ignore_index = True)
        order1 = [type+prep1 for type in self.column_types]
        order2 = [type+prep2 for type in self.column_types]
        order3 = [type+prep3 for type in self.column_types]
        self.custome_order = [val for pair in zip(order1, order2,order3) for val in pair]
        self.split = 3
        sns.set_palette(sns.color_palette(['#60EFFF','#2EA5FF','#0061FF','#D7FCCA','#73D16F','#13A718','#CD76D6','#E54678','#FF0F0F']))
        fig = self._get_fig_offset_box(offset_table, title = title)
        self.figs.append(fig)
        return fig

    def plot_two_com_dict_list_against_reference(self,comlists,reference,title):
        fig = self.get_fig_two_com_dict_list_against_reference(comlists,reference,title)
        plt.show()

    def plot_offset_between_two_com_sets(self,com1,com2,title):
        """plot_offset_between_two_com_sets [plots the offset of corresponding elements in two list of com dictionaries]

        :param com1: [list of com dicts]
        :type com1: [list]
        :param com2: [second list of com dicts]
        :type com2: [list]
        :param title: [title of the plot]
        :type title: [string]
        """
        offset_table = self._get_offset_table_from_two_com_sets(com1,com2)
        self._plot_offset_box(offset_table, title = title)

    def plot_offset_from_offset_arrays(self,offsets,title):
        """plot_offset_from_offset_arrays [generate box plot from precomputed array of offsets between coms]

        :param offsets: [array of offsets for each com]
        :type offsets: [np.array]
        :param title: [title of the plot]
        :type title: [string]
        """
        offset_table = self._get_offset_table_from_offset_array(offsets)
        self._plot_offset_box(offset_table, title = title)

    def plot_offset_from_coms_to_a_reference(self,coms,reference,title):
        """plot_offset_from_coms_to_a_reference [show box plot of com offsets between com dictionaries in a list and a reference com dictionary]

        :param coms: [list of com dictionary]
        :type coms: [list]
        :param reference: [com dictionary]
        :type reference: [dict]
        :param title: [title of plot]
        :type title: [str]
        """
        offset_table = self._get_offset_table_from_coms_to_a_reference(coms,reference)
        self._plot_offset_box(offset_table, title = title)

    def get_fig_offset_between_two_com_sets(self,com1,com2,title):
        """gets the plot of plot_offset_between_two_com_sets without plottting, good for saving pdfs"""
        offset_table = self._get_offset_table_from_two_com_sets(com1,com2)
        fig = self._get_fig_offset_box(offset_table, title = title)
        self.figs.append(fig)
        return fig

    def get_fig_offset_from_offset_arrays(self,offsets,title):
        """gets the plot of plot_offset_from_offset_arrays without plottting, good for saving pdfs"""
        offset_table = self._get_offset_table_from_offset_array(offsets)
        fig = self._get_fig_offset_box(offset_table, title = title)
        self.figs.append(fig)
        return fig

    def get_fig_offset_from_coms_to_a_reference(self,coms,reference,title):
        """gets the plot of plot_offset_from_coms_to_a_reference without plottting, good for saving pdfs"""
        offset_table = self._get_offset_table_from_coms_to_a_reference(coms,reference)
        fig = self._get_fig_offset_box(offsets_table = offset_table,title = title)
        self.figs.append(fig)
        return fig

    def save_pdf(self,file_name, folder = ''):
        """save_pdf [saves the figure in the current lists to pdf in ~/plots/foldername/filename.pdf,
        modify save_figures_to_pdf to save plots in other directories ]

        :param file_name: [pdf save file name]
        :type file_name: str, required
        :param folder: [plot folder name,saves in plots/ if left as default], defaults to ''
        :type folder: str, optional
        """
        save_figures_to_pdf(self.figs,file_name=file_name,folder=folder)

    def _get_offset_table_from_coms_to_a_reference(self,coms,reference):
        """Gets the offset table when comparing a list of coms to a reference"""
        offset_table = self._get_offset_table(coms,reference,self._get_offseti_from_com_list_and_reference)
        return offset_table

    def _get_offset_table_from_two_com_sets(self,com1,com2):
        """Gets the offset table when comparing two lists of coms"""
        offset_table = self._get_offset_table(com1,com2,self._get_offseti_from_two_com_lists)
        return offset_table

    def _get_offset_table_from_offset_array(self,offsets):
        """Gets the offset table when offsets are precalculated"""
        offset_function = lambda offsets,no_comparison_needed,no_landmark_list_needed,comi : offsets[comi]
        offset_table = self._get_offset_table(offsets,None,offset_function)
        return offset_table

    def _get_brain_count_per_structure(self,offset_table,landmark_list,min_brain_count = 3):
        """Adds the number of brain that have a specific landmark annotated  useful when using the union of landmarks of all brains examined"""
        dropping = []
        for landmarki in landmark_list:
            row_is_structurei = np.array(offset_table.structure == landmarki)
            brain_count = sum(offset_table.iloc[np.array(offset_table.structure== landmarki ),1].notnull())/4
            if brain_count < min_brain_count:
                dropping.append(np.where(row_is_structurei)[0])
            else:
                offset_table.iloc[row_is_structurei,0] = landmarki + f'({int(brain_count)})'
        if len(dropping)>0:
            offset_table.drop(np.concatenate(dropping),axis = 0, inplace = True)
        return offset_table

    def _get_offset_table(self,com1,com2,offset_function):
        """_get_offset_table [generates the offset table]

        :param com1: [a list of com dicts or a single com dict]
        :type com1: [list or dict]
        :param com2: [a list of com dicts or a single com dict]
        :type com2: [list or dict]
        :param offset_function: [this functions handles the cases when com1 and com2 are lists or dictionaries according to use case]
        :type offset_function: [function]
        :return: [offset_table]
        :rtype: [DataFrame]
        """
        prep_list = self.prep_list_function()
        landmarks = self.landmark_list_function(prep_list)
        offset_table = pd.DataFrame()
        prepi = 0
        for comi in range(len(com1)):
            offset = offset_function(com1,com2,landmarks,comi)
            offset_table_entry = self._get_offset_table_entry(offset,landmarks)
            offset_table_entry['brain'] = prep_list[prepi]
            offset_table = offset_table.append(offset_table_entry, ignore_index=True)
            prepi+=1
        offset_table = self._get_brain_count_per_structure(offset_table,landmarks)
        offset_table.type = offset_table.type.astype(str) + self.postfix
        return offset_table

    def _get_offseti_from_com_list_and_reference(self,coms,reference,landmarks,comi):
        """coms correspond to com1 and reference correspond to com2.  Handles the case when a list of com dictionaries are compares to a single reference com"""
        offset = [np.array(coms[comi][s]) - np.array(reference[s])
                    if s in coms[comi] and s in reference  else [np.nan, np.nan, np.nan]
                    for s in landmarks]
        return offset

    def _get_offseti_from_two_com_lists(self,com1,com2,landmarks,comi):
        """handles the case when comparing corresponding elements of two com lists"""
        offset = [np.array(com1[comi][s]) - np.array(com2[comi][s])
                    if s in com1[comi] and s in com2[comi] else [np.nan, np.nan, np.nan]
                    for s in landmarks]
        return offset

    def _get_offset_table_entry(self,offset,landmarks):
        """_get_offset_table_entry [function to obtain one row of table entry from calculated offsets]

        :param offset: [np array]
        :type offset: [array]
        :param landmarks: [list of landmarks]
        :type landmarks: [list]
        :return: [one chunk of the dataframe table]
        :rtype: [DataFrame]
        """
        offset = np.array(offset)
        dx, dy, dz = offset.T
        dist = np.sqrt(dx * dx + dy * dy + dz * dz)
        df_brain = pd.DataFrame()
        for data_type in self.column_types:
            data = {}
            data['structure'] = landmarks
            data['value'] = eval(data_type)
            data['type'] = data_type
            df_brain = df_brain.append(pd.DataFrame(data), ignore_index=True)
        return df_brain

    def _get_fig_offset_box(self,offsets_table, title = ''):
        """_get_fig_offset_box [main function to create the box plot adopted from Bili]

        :param offsets_table: [pandas tables with columns   "structure":structure names, "value":offset values,
                                                            "type":offset type(x,y,z direction or total distance)
                                                            "brain":the brain where coms comes from]
        :type offsets_table: [pandas.DataFrame]
        :param title: [title of plot], defaults to ''
        :type title: str, optional
        :return: [plt figure]
        :rtype: [figure object]
        """
        if self.split:
            fig, ax = plt.subplots(2*self.split, 1, figsize=(16, 12), dpi=200,constrained_layout=True)
            plit_len = len(offsets_table.structure.unique())//self.split
            split_table = []
            for spliti in range(self.split):
                split_start = plit_len*spliti
                split_end = plit_len*(spliti+1)
                split_structures = offsets_table.structure[split_start:split_end]
                is_in_split = [stri in split_structures.to_list() for stri in offsets_table.structure]
                split_table.append(offsets_table[is_in_split])
            for spliti in range(self.split):
                self._populate_figure(ax[spliti*2:(spliti+1)*2],split_table[spliti],title)
        else:
            # fig, ax = plt.subplots(2, 1, figsize=(8, self.split), dpi=200,constrained_layout=True)
            fig, ax = plt.subplots(2, 1, figsize=(16, 12*2*self.split))
            self._populate_figure(ax,offsets_table,title)
        for axi in ax:
            axi.tick_params(axis='x', labelrotation=45)
            axi.grid()
            axi.legend(loc='upper right')
        return fig

    def _plot_offset_box(self,offset_table, title = ''):
        """An alternative to plot the figure right away"""
        fig = self._get_fig_offset_box(offset_table, title = title)
        plt.show()

    def _populate_figure(self,ax,offsets_table,title):
        ymin = -500
        ymax = 500
        ystep = 100
        if self.custome_order:
            sns.boxplot(ax=ax[0], x="structure", y="value", hue="type",hue_order = self.custome_order, data=offsets_table)
        else:
            sns.boxplot(ax=ax[0], x="structure", y="value", hue="type", data=offsets_table)
        ax[0].xaxis.grid(True)
        ax[0].set_xlabel('Structure')
        ax[0].set_ylabel('um')
        ax[0].set_title(title)
        # sns.set_palette(self.color_list)
        if self.custome_order:
            sns.boxplot(ax=ax[1], x="structure", y="value", hue="type",hue_order = self.custome_order, data=offsets_table)
        else:
            sns.boxplot(ax=ax[1], x="structure", y="value", hue="type", data=offsets_table)
        sns.set_palette(sns.color_palette((self.color_list)))
        ax[1].xaxis.grid(True)
        ax[1].set_ylim(ymin, ymax)
        ax[1].yaxis.set_ticks(np.arange(ymin, ymax + 1, ystep))
        ax[0].set_xlabel('Structure')
        ax[1].set_ylabel('um')
        ax[1].set_title(title+' zoomed in')
        # sns.set_palette(self.color_list)

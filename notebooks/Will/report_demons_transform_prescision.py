from notebooks.Will.toolbox.plotting.plot_transformation_prescision import prepare_table_for_plot,plot
df = prepare_table_for_plot()
fig = plot(df, -1000, 1000, 100, 'Rigid Alignment Error After Correction')
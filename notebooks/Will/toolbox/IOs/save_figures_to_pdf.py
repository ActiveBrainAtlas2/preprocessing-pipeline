from matplotlib.backends.backend_pdf import PdfPages
from notebooks.Will.toolbox.IOs.get_plot_save_path import get_plot_save_path_pdf


def save_figures_to_pdf(figures,file_name,folder):
    save_path = get_plot_save_path_pdf(folder = folder,file_name = file_name)
    with PdfPages(save_path) as pdf:
        for fig in figures:
            pdf.savefig(fig)
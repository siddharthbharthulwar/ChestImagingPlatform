import numpy as np
from scipy.stats import mode, kurtosis, skew
from optparse import OptionParser
import nrrd
from cip_python.phenotypes.phenotypes import Phenotypes
from cip_python.utils.region_type_parser import RegionTypeParser
from cip_python.ChestConventions import ChestConventions
import pdb

class ParenchymaPhenotypes(Phenotypes):
    """General purpose class for generating parenchyma-based phenotypes.

    The user can specify chest regions, chest types, or region-type pairs over
    which to compute the phenotypes. Otherwise, the phenotypes will be computed
    over all structures in the specified labelmap. The following phenotypes are
    computed using the 'execute' method:
    'LAA950': fraction of the structure's region with CT HU values <= -950
    'LAA910': fraction of the structure's region with CT HU values <= -910
    'LAA856': fraction of the structure's region with CT HU values <= -856
    'HAA700': fraction of the structure's region with CT HU values >= -700
    'HAA600': fraction of the structure's region with CT HU values >= -600
    'HAA500': fraction of the structure's region with CT HU values >= -500
    'HAA250': fraction of the structure's region with CT HU values >= -250
    'Perc10': HU value at the 10th percentile of the structure's HU histogram
    'Perc15': HU value at the 15th percentile of the structure's HU histogram
    'HUMean': Mean value of the structure's HU values
    'HUStd': Standard deviation of the structure's HU values
    'HUKurtosis': Kurtosis of the structure's HU values. Fisher's definition is
    used, meaning that normal distribution has kurtosis of 0. The calculation
    is corrected for statistical bias.
    'HUSkewness': Skewness of the structure's HU values. The calculation is
    corrected for statistical bias.
    'HUMode': Mode of the structure's HU values
    'HUMedian': Median of the structure's HU values
    'HUMin': Min HU value for the structure
    'HUMax': Max HU value for the structure
    'HUMean500': Mean CT value of the structure, but only considering CT
    values that are <= -500 HU
    'HUStd500': Standard deviation of the structure's CT values, but only
    considering CT values that are <= -500 HU
    'HUKurtosis500': Kurtosis of the structure's HU values, but only
    considering CT values that are <= -500 HU
    'HUSkewness500': Skewness of the structure's HU values, but only
    considering CT values that are <= -500 HU
    'HUMode500': Mode of the structure's HU values, but only
    considering CT values that are <= -500 HU
    'HUMedian500': Median of the structure's HU values, but only
    considering CT values that are <= -500 HU
    'HUMin500': Min HU value for the structure, but only considering CT values
    that are <= -500 HU
    'HUMax500': Max HU value for the structure, but only considering CT values
    that are <= -500 HU
    'Volume': Volume of the structure, measured in liters
    'Mass': Mass of the structure measure in grams    

    Parameters
    ----------
    chest_regions : array, shape ( R ), optional
        Array of integers, with each element in the interval [0, 255],
        indicating the chest regions over which to compute the phenotypes.

    chest_types : array, shape ( T ), optional
        Array of integers, with each element in the interval [0, 255],
        indicating the chest types over which to compute the phenotypes.

    pairs : array, shape ( P, 2 ), optional
        Array of chest-region chest-type pairs over which to compute the
        phenotypes. The first column indicates the chest region, and the
        second column indicates the chest type. Each element should be in the
        interal [0, 255].

    pheno_names : list of strings, optional
        Names of phenotypes to compute. These names must conform to the
        accepted phenotype names, listed above. If none are given, all
        will be computed.
    """
    def __init__(self, chest_regions=None, chest_types=None, pairs=None,
                 pheno_names=None):
        if chest_regions is not None:
            if len(chest_regions.shape) != 1:
                raise ValueError(\
                'chest_regions must be a 1D array with elements in [0, 255]')
            if np.max(chest_regions) > 255 or np.min(chest_regions) < 0:
                raise ValueError(\
                'chest_regions must be a 1D array with elements in [0, 255]')
        if chest_types is not None:
            if len(chest_types.shape) != 1:
                raise ValueError(\
                'chest_types must be a 1D array with elements in [0, 255]')
            if np.max(chest_types) > 255 or np.min(chest_types) < 0:
                raise ValueError(\
                'chest_types must be a 1D array with elements in [0, 255]')
        if pairs is not None:
            if len(pairs.shape) != 2:
                raise ValueError(\
                'cpairs must be a 1D array with elements in [0, 255]')
            if np.max(chest_types) > 255 or np.min(chest_types) < 0:
                raise ValueError(\
                'chest_types must be a 1D array with elements in [0, 255]')
                
        self.chest_regions_ = chest_regions
        self.chest_types_ = chest_types
        self.pairs_ = pairs
        self.requested_pheno_names = pheno_names

        Phenotypes.__init__(self)    

    def declare_pheno_names(self):
        """Creates the names of the phenotypes to compute

        Returns
        -------
        names : list of strings
            Phenotype names
        """
        names = ['LAA950', 'LAA910', 'LAA856', 'HAA700', 'HAA600', 'HAA500',
                 'HAA250', 'Perc10', 'Perc15', 'HUMean', 'HUStd', 'HUKurtosis',
                 'HUSkewness', 'HUMode', 'HUMedian', 'HUMin', 'HUMax',
                 'HUMean500', 'HUStd500', 'HUKurtosis500', 'HUSkewness500',
                 'HUMode500', 'HUMedian500', 'HUMin500', 'HUMax500', 'Volume',
                 'Mass']
        
        return names

    def get_cid(self):
        """Get the case ID (CID)

        Returns
        -------
        cid : string
            The case ID (CID)
        """
        return self.cid_

    def execute(self, ct, lm, cid, spacing, chest_regions=None,
                chest_types=None, pairs=None, pheno_names=None):
        """Compute the phenotypes for the specified structures for the
        specified threshold values.

        The following values are computed for the specified structures.
        'LAA950': fraction of the structure's region with CT HU values <= -950
        'LAA910': fraction of the structure's region with CT HU values <= -910
        'LAA856': fraction of the structure's region with CT HU values <= -856
        'HAA700': fraction of the structure's region with CT HU values >= -700
        'HAA600': fraction of the structure's region with CT HU values >= -600
        'HAA500': fraction of the structure's region with CT HU values >= -500
        'HAA250': fraction of the structure's region with CT HU values >= -250
        'Perc10': HU value at the 10th percentile of the structure's HU
        histogram
        'Perc15': HU value at the 15th percentile of the structure's HU
        histogram
        'HUMean': Mean value of the structure's HU values
        'HUStd': Standard deviation of the structure's HU values
        'HUKurtosis': Kurtosis of the structure's HU values. Fisher's definition
        is used, meaning that normal distribution has kurtosis of 0. The
        calculation is corrected for statistical bias.
        'HUSkewness': Skewness of the structure's HU values. The calculation is
        corrected for statistical bias.
        'HUMode': Mode of the structure's HU values
        'HUMedian': Median of the structure's HU values
        'HUMin': Min HU value for the structure
        'HUMax': Max HU value for the structure
        'HUMean500': Mean CT value of the structure, but only considering CT
        values that are <= -500 HU
        'HUStd500': Standard deviation of the structure's CT values, but only
        considering CT values that are <= -500 HU
        'HUKurtosis500': Kurtosis of the structure's HU values, but only
        considering CT values that are <= -500 HU
        'HUSkewness500': Skewness of the structure's HU values, but only
        considering CT values that are <= -500 HU
        'HUMode500': Mode of the structure's HU values, but only
        considering CT values that are <= -500 HU
        'HUMedian500': Median of the structure's HU values, but only
        considering CT values that are <= -500 HU
        'HUMin500': Min HU value for the structure, but only considering CT
        values that are <= -500 HU
        'HUMax500': Max HU value for the structure, but only considering CT
        values that are <= -500 HU
        'Volume': Volume of the structure, measured in liters
        'Mass': Mass of the structure measure in grams    

        Parameters
        ----------
        ct : array, shape ( X, Y, Z )
            The 3D CT image array

        lm : array, shape ( X, Y, Z )
            The 3D label map array

        cid : string
            Case ID

        spacing : array, shape ( 3 )
            The x, y, and z spacing, respectively, of the CT volume
            
        chest_regions : array, shape ( R ), optional
            Array of integers, with each element in the interval [0, 255],
            indicating the chest regions over which to compute the LAA. If none
            specified, the chest regions specified in the class constructor
            will be used. If chest regions, chest types, and chest pairs are
            left unspecified both here and in the constructor, then the
            complete set of entities found in the label map will be used.

        chest_types : array, shape ( T ), optional
            Array of integers, with each element in the interval [0, 255],
            indicating the chest types over which to compute the LAA. If none
            specified, the chest types specified in the class constructor
            will be used. If chest regions, chest types, and chest pairs are
            left unspecified both here and in the constructor, then the
            complete set of entities found in the label map will be used.

        pairs : array, shape ( P, 2 ), optional
            Array of chest-region chest-type pairs over which to compute the
            LAA. The first column indicates the chest region, and the second
            column indicates the chest type. Each element should be in the
            interal [0, 255]. If none specified, the pairs specified in the
            class constructor will be used. If chest regions, chest types, and
            chest pairs are left unspecified both here and in the constructor,
            then the complete set of entities found in the label map will be
            used.

        pheno_names : list of strings, optional
            Names of phenotypes to compute. These names must conform to the
            accepted phenotype names, listed above. If none are given, all
            will be computed. Specified names given here will take precedence
            over any specified in the constructor.

        Returns
        -------
        df : pandas dataframe
            Dataframe containing info about machine, run time, and chest region
            chest type phenotype quantities.         
        """
        assert len(ct.shape) == len(lm.shape), \
            "CT and label map are not the same dimension"    

        dim = len(ct.shape)
        for i in xrange(0, dim):
            assert ct.shape[0] == lm.shape[0], \
                "Disagreement in CT and label map dimension"

        assert type(cid) == str, "cid must be a string"
        self.cid_ = cid
        self._spacing = spacing

        phenos_to_compute = self.pheno_names_
        if pheno_names is not None:
            phenos_to_compute = pheno_names
        elif self.requested_pheno_names is not None:
            phenos_to_compute = self.requested_pheno_names

        rs = None
        ts = None
        ps = None
        if chest_regions is not None:
            rs = chest_regions
        elif self.chest_regions_ is not None:
            rs = self.chest_regions_
        if chest_types is not None:
            ts = chest_types
        elif self.chest_types_ is not None:
            ts = self.chest_types_
        if pairs is not None:
            ps = pairs
        elif self.pairs_ is not None:
            ps = self.pairs_

        parser = RegionTypeParser(lm)
        if rs == None and ts == None and ps == None:
            rs = parser.get_all_chest_regions()
            ts = parser.get_chest_types()
            ps = parser.get_all_pairs()

        # Now compute the phenotypes and populate the data frame
        c = ChestConventions()
        if rs is not None:
            for r in rs:
                if r != 0:
                    mask = parser.get_mask(chest_region=r)
                    for n in phenos_to_compute:
                        self.add_pheno_group(ct, mask, c.GetChestRegionName(r),
                                             c.GetChestWildCardName(), n)
        if ts is not None:
            for t in ts:
                if t != 0:
                    mask = parser.get_mask(chest_type=t)
                    for n in phenos_to_compute:
                        self.add_pheno_group(ct, mask, c.GetChestWildCardName(),
                                             c.GetChestTypeName(r), n)
        if ps is not None:
            for p in ps:            
                if not (p[0] == 0 and p[1] == 0):
                    mask = parser.get_mask(chest_region=p[0], chest_type=p[1])
                    for n in phenos_to_compute:
                        self.add_pheno_group(ct, mask,
                            c.GetChestRegionName(p[0]),
                            c.GetChestTypeName(p[1]), n)

        return self._df

    def add_pheno_group(self, ct, mask, chest_region, chest_type, pheno_name):
        """For a given mask, this function computes all phenotypes corresponding
        to the masked structure and adds them to the dataframe with the
        'add_pheno' method

        Parameters
        ----------
        ct : array, shape ( X, Y, Z )
            The 3D CT image array

        mask : boolean array, shape ( X, Y, Z )
            Boolean mask where True values indicate presence of the structure
            of interest

        chest_region : string
            Name of the chest region in the (region, type) key used to populate
            the dataframe

        chest_type : string
            Name of the chest region in the (region, type) key used to populate
            the dataframe

        pheno_name : string
            Name of the phenotype used to populate the dataframe

        References
        ----------
        1. Schneider et al, 'Correlation between CT numbers and tissue
        parameters needed for Monte Carlo simulations of clinical dose
        distributions'
        """
        assert pheno_name in self.pheno_names_, "Invalid phenotype name"

        pheno_val = None
        mask_sum = np.sum(mask)
        if pheno_name == 'LAA950':
            pheno_val = float(np.sum(ct[mask] <= -950.))/mask_sum
        elif pheno_name == 'LAA910':
            pheno_val = float(np.sum(ct[mask] <= -910.))/mask_sum            
        elif pheno_name == 'LAA856':
            pheno_val = float(np.sum(ct[mask] <= -856.))/mask_sum            
        elif pheno_name == 'HAA700':
            pheno_val = float(np.sum(ct[mask] >= -700.))/mask_sum            
        elif pheno_name == 'HAA600':
            pheno_val = float(np.sum(ct[mask] >= -600))/mask_sum            
        elif pheno_name == 'HAA500':
            pheno_val = float(np.sum(ct[mask] >= -500))/mask_sum
        elif pheno_name == 'HAA250':
            pheno_val = float(np.sum(ct[mask] >= -250))/mask_sum            
        elif pheno_name == 'Perc15':
            pheno_val = np.percentile(ct[mask], 15)
        elif pheno_name == 'Perc10':
            pheno_val = np.percentile(ct[mask], 10)            
        elif pheno_name == 'HUMean':
            pheno_val = np.mean(ct[mask])
        elif pheno_name == 'HUStd':
            pheno_val = np.std(ct[mask])
        elif pheno_name == 'HUKurtosis':
            pheno_val = kurtosis(ct[mask], bias=False, fisher=True)
        elif pheno_name == 'HUSkewness':
            pheno_val = skew(ct[mask], bias=False)
        elif pheno_name == 'HUMode':
            pheno_val = mode(ct[mask])[0][0]
        elif pheno_name == 'HUMedian':
            pheno_val = np.median(ct[mask])
        elif pheno_name == 'HUMin':
            pheno_val = np.min(ct[mask])
        elif pheno_name == 'HUMax':
            pheno_val = np.max(ct[mask])
        elif pheno_name == 'HUMean500':
            hus = ct[np.logical_and(mask, ct <= -500)]
            if hus.shape[0] > 0:
                pheno_val = np.mean(hus)
        elif pheno_name == 'HUStd500':
            hus = ct[np.logical_and(mask, ct <= -500)]
            if hus.shape[0] > 0:
                pheno_val = np.std(hus)
        elif pheno_name == 'HUKurtosis500':            
            hus = ct[np.logical_and(mask, ct <= -500)]
            if hus.shape[0]:
                pheno_val = kurtosis(hus, bias=False, fisher=True)
        elif pheno_name == 'HUSkewness500':
            hus = ct[np.logical_and(mask, ct <= -500)]
            if hus.shape[0] > 0:
                pheno_val = skew(hus, bias=False)
        elif pheno_name == 'HUMode500':
            hus = ct[np.logical_and(mask, ct <= -500)]
            if hus.shape[0] > 0:
                pheno_val = mode(hus)[0][0]
        elif pheno_name == 'HUMedian500':
            hus = ct[np.logical_and(mask, ct <= -500)]
            if hus.shape[0] > 0:
                pheno_val = np.median(hus)
        elif pheno_name == 'HUMin500':
            hus = ct[np.logical_and(mask, ct <= -500)]
            if hus.shape[0] > 0:
                pheno_val = np.min(hus)
        elif pheno_name == 'HUMax500':
            hus = ct[np.logical_and(mask, ct <= -500)]
            if hus.shape[0] > 0:
                pheno_val = np.max(hus)
        elif pheno_name == 'Volume':
            pheno_val = np.prod(self._spacing)*float(mask_sum)
        elif pheno_name == 'Mass':
            # This quantity is computed in a piecewise linear form according
            # to the prescription presented in ref. [1]. Mass is computed in
            # grams. First compute the contribution in HU interval from -98
            # and below.
            pheno_val = 0.0
            HU_tmp = ct[np.logical_and(mask, ct < -98)].clip(-1000)
            if HU_tmp.shape[0] > 0:
                m = (1.21e-3-0.93)/(-1000+98)
                b = 1.21e-3 + 1000*m
                pheno_val += np.sum((m*HU_tmp + b)*\
                    np.prod(self._spacing)*0.001)

            # Now compute the mass contribution in the interval [-98, 18] HU.
            # Note the in the original paper, the interval is defined from
            # -98HU to 14HU, but we extend in slightly here so there are no
            # gaps in coverage. The values we report in the interval [14, 23]
            # should be viewed as approximate.
            HU_tmp = ct[np.logical_and(np.logical_and(mask, ct >= -98),
                                       ct <= 18)]
            if HU_tmp.shape[0] > 0:
                pheno_val += np.sum((1.018 + 0.893*HU_tmp/1000.0)*\
                    np.prod(self._spacing)*0.001)

            # Compute the mass contribution in the interval (18, 100]
            HU_tmp = ct[np.logical_and(np.logical_and(mask, ct > 18),
                                       ct <= 100)]
            if HU_tmp.shape[0] > 0:
                pheno_val += np.sum((1.003 + 1.169*HU_tmp/1000.0)*\
                    np.prod(self._spacing)*0.001)

            # Compute the mass contribution in the interval > 100
            HU_tmp = ct[np.logical_and(mask, ct > 100)]
            if HU_tmp.shape[0] > 0:
                pheno_val += np.sum((1.017 + 0.592*HU_tmp/1000.0)*\
                    np.prod(self._spacing)*0.001)

        if pheno_val is not None:
            self.add_pheno([chest_region, chest_type], pheno_name, pheno_val)

if __name__ == "__main__":
    desc = """Generates parenchyma phenotypes given input CT and segmentation \
    data"""
    
    parser = OptionParser(description=desc)
    parser.add_option('--in_ct',
                      help='Input CT file', dest='in_ct', metavar='<string>',
                      default=None)
    parser.add_option('--in_lm',
                      help='Input label map containing structures of interest',
                      dest='in_lm', metavar='<string>', default=None)
    parser.add_option('--out_csv',
                      help='Output csv file in which to store the computed \
                      dataframe', dest='out_csv', metavar='<string>',
                      default=None)
    parser.add_option('--cid',
                      help='The case ID', dest='cid', metavar='<string>',
                      default=None)    

    (options, args) = parser.parse_args()

    lm, lm_header = nrrd.read(options.in_lm)
    ct, ct_header = nrrd.read(options.in_ct)

    spacing = np.zeros(3)
    spacing[0] = ct_header['space directions'][0][0]
    spacing[1] = ct_header['space directions'][1][1]
    spacing[2] = ct_header['space directions'][2][2]

    paren_pheno = ParenchymaPhenotypes()    
    df = paren_pheno.execute(ct, lm, options.cid, spacing)
    if options.out_csv is not None:
        df.to_csv(options.out_csv)

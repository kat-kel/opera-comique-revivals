# Analysis of opéra-comique corpus, 1800-1840

A Principal Component Analysis (PCA) about operas' deployment of various instruments shows a gradual shift in the performing forces that scores required between 1800 and 1840 at the Opéra-Comique.

## Data

A digitization was located for N number of Z operas composed at the Opéra-Comique between the start of 1820 and the end of 1840.

An MEI-XML header was then generated for each digitized opera score. The header features a `<workList>`, which lists each of the opera's numbers (`<work>`). Every `<work>` contains a list of its performing forces. Encoded with the `<perfRes>` tag, the performing force includes 3 pieces of information:

1. `@codedval`: A standardized category label for the instrument, taken from the [MARC Instruments and Voices Code List](https://www.loc.gov/standards/valuelist/marcmusperf.html).

2. `@count`: The minimal number of players required for the instrument part, as determined by the number of staves (note: currently, this is an estimation, more granular encoding is needed).

3. `text`: The name of the instrument in the encoded score.

### Example: `<work>` encoding

```xml
<work n="3" xml:id="work3">
    <title>Air</title>
    <incip>
        <incipText>
            <p>De tous les pays pour vous plaire</p>
        </incipText>
    </incip>
    <perfMedium>
        <perfResList>
            <perfRes count="1" codedval="wa">Flutes</perfRes>
            <perfRes count="1" codedval="we">Petite flute</perfRes>
            <perfRes count="1" codedval="wc">Clarinettes</perfRes>
            <perfRes count="1" codedval="ba">Cors in D</perfRes>
            <perfRes count="1" codedval="wd">Fag.</perfRes>
            <perfRes count="2" codedval="sa">Viol.</perfRes>
            <perfRes count="1" codedval="sb">Alto</perfRes>
            <perfRes count="1" codedval="sn">Bassi</perfRes>
        </perfResList>
    </perfMedium>
</work>
```

The corpus of encoded MEI-XML headers was then processed into a dataset that presents how much of the opera required at least 1 of each instrument. This representation is calculated as the sum of times 1 or more instruments are required for a work, divided by the quantity of works. Because the `@count` metadata is not yet reliable, it is ignored. Any time an instrument is required, 1 value is added to the sum of times the instrument is required during the opera. The sum is divided by the quantity of works in order to standardize the average for operas in the corpus of varying lengths. An example of the resulting dataset is shown below.

### Example: Selection from dataset

- 1800: _Les Deux Journées ou le Porteur d'eau_ (Cherubini)
- 1823: _Leicester ou le Château de Kenilworth_ (Auber)
- 1840: _Zanetta ou Jouer avec le feu_ (Auber)

year|Brass: Horn|Brass: Trumpet|Brass: Cornet|Brass: Trombone|Brass: Baritone (Ophicleide)|Keyboard: Piano|Keyboard: Organ|Percussion: Timpani|Percussion: Drum|Percussion: Other|Strings, bowed: Violin|Strings, bowed: Viola|Strings, bowed: Violoncello|Strings, bowed: Double bass|Strings, bowed: Unspecified|Strings, plucked: Harp|Woodwinds: Flute|Woodwinds: Oboe|Woodwinds: Clarinet|Woodwinds: Bassoon|Woodwinds: Piccolo|Woodwinds: Bass clarinet
-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-
1800|0.86|0.0|0.0|0.43|0.0|0.0|0.0|0.14|0.0|0.0|1.0|1.0|0.86|0.5|0.36|0.0|0.79|0.71|0.71|0.86|0.0|0.0
1823|1.0|0.53|0.0|0.0|0.0|0.0|0.0|0.4|0.0|0.0|1.0|1.0|1.0|1.0|0.0|0.27|1.0|1.0|1.0|0.0|0.2|0.0
1840|1.0|0.47|0.07|0.8|0.0|0.0|0.0|0.53|0.13|0.13|1.0|1.0|1.0|1.0|0.0|0.0|1.0|1.0|1.0|1.0|0.4|0.0

## Methodology

The challenge with analyzing instrumentation is that each opera has a high number of dimensions, as many as there are instruments in the orchestra. Using PCA, we can reduce the data to what is most important and plot the operas along 2 dimensions, rendering it comprehensible to a human.

Violins and violas, for example, were used in every number of every opera in the corpus. Therefore, as seen in the heatmap in the figure below, they are both highly correlated with one of the principal components and hardly correlated at all (0.02 and 0.07) with the other. This means that the presence of violons and violas is not a significant factor in the analysis. Trombones, trumpets, and timpani, on the other hand, are significant in both principal components of the analysis, both negatively (magenta) and positively (purple) influencing the PCA. Therefore, we can conclude that these dimensions, low brass and percussion, have significant deviations in the corpus.

![PCA variable weights](results/pca_variables_and_components.png?)

When we plot the operas in a 2-D graph according to their PCA values (PCA1, PCA2), we see clusters form according to the opera's year of composition, which is indicated by color. This is interesting because the year of composition is not part of the PCA; it is a completely independent variable. As such, we can conclude that patterns in opera orchestration, which the PCA explores, are correlated with time. In other words, orchestration changes over time. (This is what we predicted in our hypothesis and, on its own, isn't surprising at all.)

![PCA plot](results/pca_plot.png?)

Operas composed between 1815 and 1825, shown in yellow, are less predicatbly positioned in the PCA visualization, especially compared to the operas composed in the following decades. Sometimes operas composed during this transition period cluster with those of the previous decade. Such is the case of _Le Pavillon de fleurs_ (1822), _Les Rivaux de village_ (1819), and _Corisandre ou la Rose magique_ (1820). Yet, other times, they do not share many traits with operas on either end of the temporal spectrum, as seen with the yellow cluster at the center of the graph. Further inspection of these operas, which date primarily from between 1817 and 1823, shows that the reason they differ is because they tended to deploy trumpets, unlike earlier operas, but not trombones, unlike later operas.

Most of the operas composed after 1830 are tightly grouped together in a shared, almost standardized instrumentation. They appear in a blue-green cluster with PCA1 values between 1.5 and 4, and PCA2 values between -1 and 1. However, there are several notable outliers from this time period that differ both from previous models and contemporary operas: _Le Domino Noir_ (1837), _Zampa_ (1831), and _Le morceau d'ensemble_ (1831). These outliers suggest that the 1830s presented more innovative experimentations in orchestration not tested earlier in the century.

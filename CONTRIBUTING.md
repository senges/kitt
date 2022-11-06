# How to contribute

Really glad to see someone here ! 

It means you are using kitt and mostly hyped enough to contribute. Thanks alot ! :hearts:

## Commit and branching convention

Kitt repository is managed using [conventional commits](https://www.conventionalcommits.org/en/v1.0.0) convention for both commit messages and branch names.

If you are unsure how to properly follow this convention, please have a look at the documentation linked above or maybe consider using helping tools such as [cocogitto](https://github.com/cocogitto/cocogitto).

## Coding convention

Kitt does not follow any strict coding convention.

However, any contribution shall follow the basic coding principles to keep it readable and maintainable.  
As kitt is written python, that would be :

* functions and class should include a docstring
* functions signatures should include type hints for parameters and return statements
* `except` statement should be as precise as possible (avoid `except Exception`)
* avoid too many [nested statement](https://en.wikibooks.org/wiki/Computer_Programming/Coding_Style/Minimize_nesting) or any [code smell](https://fr.wikipedia.org/wiki/Code_smell) in general

Linters like [pylint](https://github.com/PyCQA/pylint) are a great help to keep code clean and consistent.
Most modern IDE have linter extentions.

**These are general rules. Yet if you are now familiar with all of them, your can submit contribution anyway ! It will be reviewed and discussed if necessary.**

## Have an idea you want to submit ?

Most of the time, **everything starts with [an issue](https://github.com/senges/kitt/issues/new)** _(does not apply for cosmetic changes and documentation)_.

Once your issue is open and properly tagged, any Pull Request is genuinely welcome !   
Don't forget to include a comprehensive list of what you've done, and what were your motivations.

A general rule to make your PR crystal clear would be keeping your commits atomic.  
You can do as much commits as you feel, as long as you follow the one-commit = one-feature rule.

`git log` should be readable as a book. If you are not happy about yours, git has a powerful [interactive rebase mode](https://www.atlassian.com/git/tutorials/rewriting-history/git-rebase).

## Not sure how to help ?

You want to provide some coding force to Kitt but do not have any particular idea on what to code ? Don't panic, we have stuff to do !

Kitt ongoing development / bug fix effort is tracked using issues. 
You can have a broader view of issues life-cycle in the [project tab](https://github.com/senges/kitt/projects).

Feel free to add, edit, suggest, assign yourself any stuff you feel is right for you !

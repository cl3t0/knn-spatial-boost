nbdev:
	@poetry run nbdev_export
	@poetry run nbdev_test
	@poetry run nbdev_clean
	@poetry run nbdev_readme